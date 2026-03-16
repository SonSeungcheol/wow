from io import BytesIO
import pandas as pd


def build_excel(payload: dict) -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        pd.DataFrame(payload["trial_balance"]).T.reset_index().to_excel(writer, sheet_name="합계잔액시산표", index=False)
        pd.DataFrame([payload["income_statement"]]).to_excel(writer, sheet_name="손익계산서", index=False)
        pd.DataFrame([payload["balance_sheet"]]).to_excel(writer, sheet_name="재무상태표", index=False)
        pd.DataFrame([payload["retained_earnings"]]).to_excel(writer, sheet_name="이익잉여금처분", index=False)
        pd.DataFrame([payload["cashflow"]]).to_excel(writer, sheet_name="현금흐름표", index=False)
    output.seek(0)
    return output.read()
