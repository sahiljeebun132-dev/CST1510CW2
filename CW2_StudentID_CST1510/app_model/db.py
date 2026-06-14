"""
db.py
-----
Database connection utility (CW2 Video 03/04).

A single place that knows where the SQLite file lives and how to open it.
Using row_factory = sqlite3.Row lets us read columns by name (row["status"])
which keeps the rest of the code readable.
"""

import os
import sqlite3

# DATA/ folder lives next to the project root (one level up from app_model/)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "DATA")
DB_PATH = os.path.join(DATA_DIR, "project_data.db")

os.makedirs(DATA_DIR, exist_ok=True)


def get_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    """Open (creating if needed) and return a SQLite connection."""
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row          # access columns by name
    conn.execute("PRAGMA foreign_keys = ON")  # enforce relationships
    return conn
