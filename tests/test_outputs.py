"""End-to-end verification for the Puzzle Tower migration."""

import hashlib
import json
import os
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.request import urlopen

import pytest


PROJECT_ROOT = Path(os.environ.get("TOWER_PROJECT_ROOT", "/app"))
DB_PATH = PROJECT_ROOT / "data" / "tower.sql"
MANIFEST_PATH = PROJECT_ROOT / "manifest.json"
API_DIR = PROJECT_ROOT / "api"


def reserve_port() -> int:
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return listener.getsockname()[1]


@pytest.fixture(scope="module")
def running_api():
    if not DB_PATH.exists():
        subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "scripts" / "init_db.py")],
            check=True,
        )

    with tempfile.TemporaryDirectory() as temporary_directory:
        port = reserve_port()
        base_url = f"http://127.0.0.1:{port}"
        environment = os.environ.copy()
        environment["TOWER_API_ADDR"] = f"127.0.0.1:{port}"
        environment["TOWER_STATE_PATH"] = str(Path(temporary_directory) / "rooms.json")
        binary_path = Path(temporary_directory) / "puzzle-api"
        subprocess.run(
            ["go", "build", "-o", str(binary_path), "."],
            cwd=API_DIR,
            env=environment,
            check=True,
        )
        process = subprocess.Popen(
            [str(binary_path)],
            env=environment,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        try:
            deadline = time.monotonic() + 20
            while time.monotonic() < deadline:
                if process.poll() is not None:
                    pytest.fail("Puzzle Tower API exited before becoming healthy")
                try:
                    with urlopen(f"{base_url}/health", timeout=0.5) as response:
                        if response.status == 200:
                            break
                except OSError:
                    time.sleep(0.1)
            else:
                pytest.fail("Puzzle Tower API did not become healthy")
            yield base_url
        finally:
            process.terminate()
            process.wait(timeout=10)


def run_migration(base_url: str) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment["TOWER_DB_PATH"] = str(DB_PATH)
    environment["TOWER_API_URL"] = base_url
    environment["TOWER_MANIFEST_PATH"] = str(MANIFEST_PATH)
    return subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "migrate.py")],
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )


def source_rooms() -> list[dict[str, int | str]]:
    with sqlite3.connect(DB_PATH) as connection:
        rows = connection.execute(
            "SELECT room_id, status, hint_unlocked FROM rooms ORDER BY room_id"
        ).fetchall()
    return [
        {"room_id": room_id, "status": status, "hint_unlocked": hint_unlocked}
        for room_id, status, hint_unlocked in rows
    ]


def api_rooms(base_url: str) -> list[dict[str, int | str]]:
    with urlopen(f"{base_url}/api/v1/rooms", timeout=5) as response:
        return json.load(response)


def test_manifest_and_api_match_source(running_api: str) -> None:
    result = run_migration(running_api)
    assert result.returncode == 0, result.stderr

    rooms = source_rooms()
    expected_checksum = hashlib.sha256(
        "".join(str(room["room_id"]) for room in rooms).encode("utf-8")
    ).hexdigest()
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    assert manifest == {
        "total_rooms_migrated": len(rooms),
        "target_checksum": expected_checksum,
    }
    assert rooms
    assert api_rooms(running_api) == rooms


def test_migration_is_idempotent(running_api: str) -> None:
    first_result = run_migration(running_api)
    second_result = run_migration(running_api)
    assert first_result.returncode == 0, first_result.stderr
    assert second_result.returncode == 0, second_result.stderr
    assert api_rooms(running_api) == source_rooms()