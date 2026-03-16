"""Financial statements generator (P/L and B/S)."""
from __future__ import annotations

import pandas as pd


def _account_type_map(accounts_df: pd.DataFrame) -> dict[str, str]:
    if accounts_df.empty:
        return {}
    return dict(zip(accounts_df["name"], accounts_df["type"]))


def income_statement(trial_balance_df: pd.DataFrame, accounts_df: pd.DataFrame) -> pd.DataFrame:
    if trial_balance_df.empty:
        return pd.DataFrame(columns=["구분", "금액"])
    type_map = _account_type_map(accounts_df)
    df = trial_balance_df.copy()
    df["type"] = df["account"].map(type_map)
    df["net"] = df["credit_total"] - df["debit_total"]

    revenue = float(df.loc[df["type"] == "수익", "net"].sum())
    expense = float((-df.loc[df["type"] == "비용", "net"]).sum())
    net_income = revenue - expense
    return pd.DataFrame([
        {"구분": "수익 합계", "금액": revenue},
        {"구분": "비용 합계", "금액": expense},
        {"구분": "당기순이익", "금액": net_income},
    ])


def balance_sheet(trial_balance_df: pd.DataFrame, accounts_df: pd.DataFrame, net_income: float) -> pd.DataFrame:
    if trial_balance_df.empty:
        return pd.DataFrame(columns=["구분", "금액"])
    type_map = _account_type_map(accounts_df)
    df = trial_balance_df.copy()
    df["type"] = df["account"].map(type_map)
    df["balance"] = df["debit_total"] - df["credit_total"]

    assets = float(df.loc[df["type"] == "자산", "balance"].sum())
    liabilities = float((-df.loc[df["type"] == "부채", "balance"]).sum())
    equity = float((-df.loc[df["type"] == "자본", "balance"]).sum()) + float(net_income)

    return pd.DataFrame([
        {"구분": "자산 합계", "금액": assets},
        {"구분": "부채 합계", "금액": liabilities},
        {"구분": "자본 합계(당기순이익 반영)", "금액": equity},
        {"구분": "부채+자본", "금액": liabilities + equity},
    ])
