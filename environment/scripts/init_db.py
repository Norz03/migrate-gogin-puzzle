"""Create or reset the local SQLite source database."""

import argparse
import sqlite3
from pathlib import Path


DB_PATH = Path(__file__).resolve().parents[1] / "data" / "tower.sql"


def initialize(reset: bool = False) -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS rooms (
                room_id INTEGER PRIMARY KEY,
                status TEXT NOT NULL CHECK (status IN ('locked', 'active', 'cleared')),
                hint_unlocked INTEGER NOT NULL CHECK (hint_unlocked IN (0, 1))
            )
            """
        )
        if reset:
            connection.execute(
                "UPDATE rooms SET status = 'locked', hint_unlocked = 0"
            )
        else:
            connection.executemany(
                "INSERT OR IGNORE INTO rooms (room_id, status, hint_unlocked) VALUES (?, ?, ?)",
                [(1, "locked", 0), (2, "locked", 0), (3, "locked", 0)],
            )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reset", action="store_true", help="reset all rooms to locked")
    initialize(parser.parse_args().reset)