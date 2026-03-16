"""Ledger and trial balance calculators."""
from __future__ import annotations

import pandas as pd


def journal_to_ledger(journal_df: pd.DataFrame) -> pd.DataFrame:
    if journal_df.empty:
        return pd.DataFrame(columns=["account", "date", "description", "debit", "credit", "balance"])

    rows = []
    for _, r in journal_df.iterrows():
        rows.append({"account": r["debit_account"], "date": r["date"], "description": r["description"], "debit": r["amount"], "credit": 0.0})
        rows.append({"account": r["credit_account"], "date": r["date"], "description": r["description"], "debit": 0.0, "credit": r["amount"]})

    ledger_df = pd.DataFrame(rows).sort_values(["account", "date"]).reset_index(drop=True)
    ledger_df["balance"] = ledger_df.groupby("account").apply(lambda g: (g["debit"] - g["credit"]).cumsum()).reset_index(level=0, drop=True)
    return ledger_df


def trial_balance(ledger_df: pd.DataFrame) -> pd.DataFrame:
    if ledger_df.empty:
        return pd.DataFrame(columns=["account", "debit_total", "credit_total"])
    tb = ledger_df.groupby("account", as_index=False).agg(debit_total=("debit", "sum"), credit_total=("credit", "sum"))
    return tb.sort_values("account").reset_index(drop=True)
