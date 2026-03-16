"""Transaction and journal entry persistence logic."""
from __future__ import annotations

import sqlite3

from core.validators import validate_journal_balance


def create_transaction(conn: sqlite3.Connection, payload: dict, status: str = "pending") -> int:
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO transactions(
            date, vendor, description, amount, payment_method, vat_included, memo, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            payload["date"],
            payload["vendor"],
            payload["description"],
            float(payload["amount"]),
            payload["payment_method"],
            int(bool(payload.get("vat_included", False))),
            payload.get("memo", ""),
            status,
        ),
    )
    conn.commit()
    return int(cur.lastrowid)


def save_journal_entry(conn: sqlite3.Connection, transaction_id: int, entry: dict, approved: bool) -> int:
    validate_journal_balance(entry["amount"], entry["amount"])
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO journal_entries(
            transaction_id, debit_account, credit_account, amount,
            explanation, review_points, approved
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            transaction_id,
            entry["debit_account"],
            entry["credit_account"],
            float(entry["amount"]),
            entry["explanation"],
            entry["review_points"],
            int(bool(approved)),
        ),
    )
    new_status = "approved" if approved else "review_needed"
    cur.execute("UPDATE transactions SET status = ? WHERE id = ?", (new_status, transaction_id))
    conn.commit()
    return int(cur.lastrowid)


def fetch_transactions(conn: sqlite3.Connection, only_pending: bool = False) -> list[sqlite3.Row]:
    cur = conn.cursor()
    if only_pending:
        cur.execute("SELECT * FROM transactions WHERE status IN ('pending', 'review_needed') ORDER BY date DESC, id DESC")
    else:
        cur.execute("SELECT * FROM transactions ORDER BY date DESC, id DESC")
    return cur.fetchall()


def fetch_journal(conn: sqlite3.Connection, approved_only: bool = True) -> list[sqlite3.Row]:
    cur = conn.cursor()
    where_clause = "WHERE je.approved = 1" if approved_only else ""
    cur.execute(
        f"""
        SELECT je.*, t.date, t.vendor, t.description
        FROM journal_entries je
        JOIN transactions t ON t.id = je.transaction_id
        {where_clause}
        ORDER BY t.date, je.id
        """
    )
    return cur.fetchall()
