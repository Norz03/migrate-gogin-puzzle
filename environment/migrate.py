"""Synchronize the legacy SQLite room table with the local Puzzle Tower API."""

import hashlib
import json
import os
import sqlite3
import sys
import tempfile
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


PROJECT_DIR = Path(__file__).resolve().parent
DEFAULT_DB_PATH = PROJECT_DIR / "data" / "tower.sql"
DEFAULT_MANIFEST_PATH = PROJECT_DIR / "manifest.json"
DEFAULT_API_URL = "http://127.0.0.1:8080"
REQUEST_TIMEOUT_SECONDS = 5


def read_rooms(database_path: Path) -> list[dict[str, int | str]]:
    """Read and validate source rows without modifying the legacy database."""
    database_uri = f"{database_path.resolve().as_uri()}?mode=ro"
    with sqlite3.connect(database_uri, uri=True) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            "SELECT room_id, status, hint_unlocked FROM rooms ORDER BY room_id ASC"
        ).fetchall()

    rooms = []
    for row in rows:
        room_id, status, hint_unlocked = row
        if not isinstance(room_id, int) or room_id <= 0:
            raise ValueError(f"Invalid room_id: {room_id!r}")
        if status not in {"locked", "active", "cleared"}:
            raise ValueError(f"Invalid status for room {room_id}: {status!r}")
        if hint_unlocked not in (0, 1):
            raise ValueError(f"Invalid hint_unlocked value for room {room_id}: {hint_unlocked!r}")
        rooms.append(
            {"room_id": room_id, "status": status, "hint_unlocked": hint_unlocked}
        )
    return rooms


def sync_room(api_url: str, room: dict[str, int | str]) -> None:
    payload = json.dumps(room).encode("utf-8")
    request = Request(
        f"{api_url.rstrip('/')}/api/v1/sync",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
        if response.status != 202:
            raise RuntimeError(
                f"API rejected room {room['room_id']} with HTTP {response.status}"
            )


def write_manifest(manifest_path: Path, room_ids: list[int]) -> None:
    checksum_input = "".join(str(room_id) for room_id in sorted(room_ids))
    manifest = {
        "total_rooms_migrated": len(room_ids),
        "target_checksum": hashlib.sha256(checksum_input.encode("utf-8")).hexdigest(),
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", dir=manifest_path.parent, delete=False
        ) as temporary_file:
            json.dump(manifest, temporary_file, indent=2)
            temporary_file.write("\n")
            temporary_path = Path(temporary_file.name)
        temporary_path.replace(manifest_path)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def run_migration(
    database_path: Path,
    api_url: str,
    manifest_path: Path,
) -> int:
    rooms = read_rooms(database_path)
    for room in rooms:
        sync_room(api_url, room)
    write_manifest(manifest_path, [int(room["room_id"]) for room in rooms])
    print(f"Migrated {len(rooms)} rooms; manifest written to {manifest_path}")
    return 0


def main() -> int:
    database_path = Path(os.environ.get("TOWER_DB_PATH", DEFAULT_DB_PATH))
    api_url = os.environ.get("TOWER_API_URL", DEFAULT_API_URL)
    manifest_path = Path(
        os.environ.get("TOWER_MANIFEST_PATH", DEFAULT_MANIFEST_PATH)
    )
    try:
        return run_migration(database_path, api_url, manifest_path)
    except (OSError, sqlite3.Error, HTTPError, URLError, ValueError, RuntimeError) as error:
        print(f"Migration failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())