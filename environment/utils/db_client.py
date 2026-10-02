"""Handles SQLite database connections safely."""
import sqlite3
from contextlib import contextmanager
from typing import Generator

@contextmanager
def get_connection(db_path: str) -> Generator[sqlite3.Connection, None, None]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()