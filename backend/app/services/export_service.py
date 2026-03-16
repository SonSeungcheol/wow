from io import BytesIO

import pandas as pd


def build_excel(payload: dict, journal_rows: list[dict], general_ledger: dict, closing_journal_rows: list[dict], tax_summary: dict) -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        pd.DataFrame(payload["trial_balance"]).T.reset_index().rename(columns={"index": "account"}).to_excel(writer, sheet_name="합계잔액시산표", index=False)
        pd.DataFrame(payload["income_statement"], index=[0]).to_excel(writer, sheet_name="손익계산서", index=False)
        pd.DataFrame(payload["balance_sheet"], index=[0]).to_excel(writer, sheet_name="재무상태표", index=False)
        pd.DataFrame(payload["retained_earnings"], index=[0]).to_excel(writer, sheet_name="이익잉여금처분", index=False)
        pd.DataFrame(payload["cashflow"], index=[0]).to_excel(writer, sheet_name="현금흐름표", index=False)
        pd.DataFrame(journal_rows).to_excel(writer, sheet_name="분개장", index=False)
        ledger_rows = []
        for account, rows in general_ledger.items():
            for row in rows:
                ledger_rows.append({"account": account, **row})
        pd.DataFrame(ledger_rows).to_excel(writer, sheet_name="총계정원장", index=False)
        pd.DataFrame(closing_journal_rows).to_excel(writer, sheet_name="결산분개장", index=False)
        pd.DataFrame([{"category": k, "amount": v} for k, v in tax_summary.items()]).to_excel(writer, sheet_name="세무조정집계", index=False)
    output.seek(0)
    return output.read()
