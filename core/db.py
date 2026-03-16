"""SQLite helpers and schema management."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path


def get_connection(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            vendor TEXT NOT NULL,
            description TEXT NOT NULL,
            amount REAL NOT NULL,
            payment_method TEXT NOT NULL,
            vat_included INTEGER NOT NULL,
            memo TEXT,
            status TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS journal_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_id INTEGER NOT NULL,
            debit_account TEXT NOT NULL,
            credit_account TEXT NOT NULL,
            amount REAL NOT NULL,
            explanation TEXT NOT NULL,
            review_points TEXT NOT NULL,
            approved INTEGER NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (transaction_id) REFERENCES transactions(id)
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL UNIQUE,
            type TEXT NOT NULL,
            active INTEGER NOT NULL
        )
        """
    )
    conn.commit()


def seed_accounts(conn: sqlite3.Connection, accounts_json_path: str) -> None:
    accounts = json.loads(Path(accounts_json_path).read_text(encoding="utf-8"))
    cur = conn.cursor()
    for acc in accounts:
        cur.execute(
            """
            INSERT OR IGNORE INTO accounts(code, name, type, active)
            VALUES (?, ?, ?, ?)
            """,
            (acc["code"], acc["name"], acc["type"], int(acc.get("active", True))),
        )
    conn.commit()
