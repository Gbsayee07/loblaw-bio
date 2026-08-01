"""Shared helper for connecting to the cell_counts.db SQLite database."""

import os
import sqlite3

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(ROOT_DIR, "cell_counts.db")
OUTPUTS_DIR = os.path.join(ROOT_DIR, "outputs")


def get_connection():
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(
            f"Database not found at {DB_PATH}. Run `python load_data.py` first."
        )
    return sqlite3.connect(DB_PATH)
