"""Excel export utility for accounting reports."""
from __future__ import annotations

from io import BytesIO

import pandas as pd


def export_reports_to_excel(dataframes: dict[str, pd.DataFrame]) -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for sheet_name, df in dataframes.items():
            safe_sheet = sheet_name[:31]
            if df is None or df.empty:
                pd.DataFrame([{"message": "데이터 없음"}]).to_excel(writer, sheet_name=safe_sheet, index=False)
            else:
                df.to_excel(writer, sheet_name=safe_sheet, index=False)
    output.seek(0)
    return output.read()
