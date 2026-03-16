from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

from ai.rule_based_engine import RuleBasedJournalEngine
from core.db import get_connection, init_db, seed_accounts
from core.journal import create_transaction, fetch_journal, fetch_transactions, save_journal_entry
from core.ledger import journal_to_ledger, trial_balance
from core.statements import balance_sheet, income_statement
from core.validators import validate_transaction_payload
from exports.excel_exporter import export_reports_to_excel

st.set_page_config(page_title="복식부기 회계 보조 MVP", layout="wide")


def load_json(path: str) -> dict | list:
    return json.loads(Path(path).read_text(encoding="utf-8"))


settings = load_json("config/settings.json")
conn = get_connection(settings["database_path"])
init_db(conn)
seed_accounts(conn, "config/accounts.json")
engine = RuleBasedJournalEngine("config/rules.json")

accounts_df = pd.read_sql_query("SELECT code, name, type, active FROM accounts WHERE active=1 ORDER BY code", conn)

st.title(f"{settings['company_name']} - 회계 보조 MVP")
st.caption(f"회계기간: {settings['fiscal_year_start']} ~ {settings['fiscal_year_end']}")

menu = st.sidebar.radio(
    "화면 선택",
    [
        "거래 입력",
        "분개 제안 검토 및 승인",
        "분개장 조회",
        "총계정원장 조회",
        "시산표 조회",
        "손익계산서 / 재무상태표",
        "Excel 다운로드",
    ],
)

if menu == "거래 입력":
    st.subheader("거래 입력")
    with st.form("tx_form"):
        c1, c2 = st.columns(2)
        date = c1.date_input("거래일자")
        vendor = c2.text_input("거래처")
        description = st.text_input("적요")
        amount = st.number_input("금액", min_value=0.0, step=1000.0)
        payment_method = st.selectbox("결제수단", ["보통예금", "카드", "현금", "외상", "미지급"])
        vat_included = st.checkbox("부가세 포함 여부", value=True)
        memo = st.text_area("메모")
        submitted = st.form_submit_button("저장 및 분개 제안 생성")

    if submitted:
        payload = {
            "date": str(date),
            "vendor": vendor.strip(),
            "description": description.strip(),
            "amount": amount,
            "payment_method": payment_method,
            "vat_included": vat_included,
            "memo": memo.strip(),
        }
        errors = validate_transaction_payload(payload)
        if errors:
            for err in errors:
                st.error(err)
        else:
            tx_id = create_transaction(conn, payload, status="pending")
            suggestion = engine.suggest(payload)
            save_journal_entry(conn, tx_id, suggestion, approved=False)
            st.success(f"거래 저장 완료 (ID: {tx_id}), 분개 제안 생성됨")
            st.json(suggestion)

elif menu == "분개 제안 검토 및 승인":
    st.subheader("분개 제안 검토")
    pending = fetch_transactions(conn, only_pending=True)
    if not pending:
        st.info("검토할 거래가 없습니다.")
    for tx in pending:
        st.markdown(f"### 거래 #{tx['id']} - {tx['date']} / {tx['vendor']}")
        st.write(f"적요: {tx['description']} / 금액: {tx['amount']:,.0f}")
        je = pd.read_sql_query("SELECT * FROM journal_entries WHERE transaction_id=? ORDER BY id DESC LIMIT 1", conn, params=[tx["id"]])
        if je.empty:
            st.warning("분개 제안 없음")
            continue
        rec = je.iloc[0]
        with st.form(f"approve_{tx['id']}"):
            account_names = accounts_df["name"].tolist()
            debit_idx = account_names.index(rec["debit_account"]) if rec["debit_account"] in account_names else 0
            credit_idx = account_names.index(rec["credit_account"]) if rec["credit_account"] in account_names else 0
            debit_account = st.selectbox("차변", account_names, index=debit_idx, key=f"d_{tx['id']}")
            credit_account = st.selectbox("대변", account_names, index=credit_idx, key=f"c_{tx['id']}")
            amount = st.number_input("금액", min_value=0.0, value=float(rec["amount"]), key=f"a_{tx['id']}")
            explanation = st.text_area("분개 이유", value=rec["explanation"], key=f"e_{tx['id']}")
            review_points = st.text_area("체크포인트", value=rec["review_points"], key=f"r_{tx['id']}")
            action = st.form_submit_button("수정 반영 후 승인")
        if action:
            update = {
                "debit_account": debit_account,
                "credit_account": credit_account,
                "amount": amount,
                "explanation": explanation,
                "review_points": review_points,
            }
            save_journal_entry(conn, tx["id"], update, approved=True)
            st.success(f"거래 #{tx['id']} 승인 저장 완료")

journal_rows = fetch_journal(conn, approved_only=True)
journal_df = pd.DataFrame([dict(r) for r in journal_rows])
if journal_df.empty:
    ledger_df = pd.DataFrame()
    tb_df = pd.DataFrame()
    pl_df = pd.DataFrame()
    bs_df = pd.DataFrame()
else:
    ledger_df = journal_to_ledger(journal_df)
    tb_df = trial_balance(ledger_df)
    pl_df = income_statement(tb_df, accounts_df)
    net_income = float(pl_df.loc[pl_df["구분"] == "당기순이익", "금액"].sum())
    bs_df = balance_sheet(tb_df, accounts_df, net_income)

if menu == "분개장 조회":
    st.subheader("분개장")
    st.dataframe(journal_df if not journal_df.empty else pd.DataFrame([{"message": "데이터 없음"}]), use_container_width=True)

elif menu == "총계정원장 조회":
    st.subheader("총계정원장")
    st.dataframe(ledger_df if not ledger_df.empty else pd.DataFrame([{"message": "데이터 없음"}]), use_container_width=True)

elif menu == "시산표 조회":
    st.subheader("시산표")
    st.dataframe(tb_df if not tb_df.empty else pd.DataFrame([{"message": "데이터 없음"}]), use_container_width=True)

elif menu == "손익계산서 / 재무상태표":
    st.subheader("손익계산서")
    st.dataframe(pl_df if not pl_df.empty else pd.DataFrame([{"message": "데이터 없음"}]), use_container_width=True)
    st.subheader("재무상태표")
    st.dataframe(bs_df if not bs_df.empty else pd.DataFrame([{"message": "데이터 없음"}]), use_container_width=True)

elif menu == "Excel 다운로드":
    st.subheader("Excel 다운로드")
    excel_bytes = export_reports_to_excel(
        {
            "journal": journal_df,
            "ledger": ledger_df,
            "trial_balance": tb_df,
            "income_statement": pl_df,
            "balance_sheet": bs_df,
        }
    )
    st.download_button(
        label="엑셀 파일 다운로드",
        data=excel_bytes,
        file_name="accounting_reports.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
