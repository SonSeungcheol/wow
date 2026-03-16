from app.services.ledger_service import LedgerService


class StatementService:
    @staticmethod
    def income_statement(tb: dict):
        revenue = sum(v["credit"] - v["debit"] for v in tb.values() if v["type"] == "수익")
        expense = sum(v["debit"] - v["credit"] for v in tb.values() if v["type"] == "비용")
        return {"revenue": round(revenue, 2), "expense": round(expense, 2), "net_income": round(revenue - expense, 2)}

    @staticmethod
    def balance_sheet(tb: dict, net_income: float):
        assets = sum(v["debit"] - v["credit"] for v in tb.values() if v["type"] == "자산")
        liabilities = sum(v["credit"] - v["debit"] for v in tb.values() if v["type"] == "부채")
        equity_base = sum(v["credit"] - v["debit"] for v in tb.values() if v["type"] == "자본")
        equity = equity_base + net_income
        return {
            "assets": round(assets, 2),
            "liabilities": round(liabilities, 2),
            "equity": round(equity, 2),
            "liabilities_and_equity": round(liabilities + equity, 2),
        }

    @staticmethod
    def retained_earnings_statement(net_income: float):
        return {"beginning": 0.0, "net_income": round(net_income, 2), "ending": round(net_income, 2)}

    @staticmethod
    def cashflow_indirect(tb: dict, net_income: float):
        depreciation = sum(v["debit"] - v["credit"] for k, v in tb.items() if "감가상각비" in k)
        delta_receivables = sum(v["debit"] - v["credit"] for k, v in tb.items() if "미수" in k)
        delta_inventory = sum(v["debit"] - v["credit"] for k, v in tb.items() if k in ("원재료", "재고자산"))
        delta_payables = sum(v["credit"] - v["debit"] for k, v in tb.items() if "미지급" in k)
        operating = net_income + depreciation - delta_receivables - delta_inventory + delta_payables
        return {
            "operating_cashflow": round(operating, 2),
            "investing_cashflow": 0.0,
            "financing_cashflow": 0.0,
            "net_change": round(operating, 2),
        }

    @staticmethod
    def statements(db, company_id: int, fiscal_year_id: int):
        tb = LedgerService.trial_balance(db, company_id, fiscal_year_id)
        pl = StatementService.income_statement(tb)
        bs = StatementService.balance_sheet(tb, pl["net_income"])
        re = StatementService.retained_earnings_statement(pl["net_income"])
        cf = StatementService.cashflow_indirect(tb, pl["net_income"])
        return {
            "trial_balance": tb,
            "income_statement": pl,
            "balance_sheet": bs,
            "retained_earnings": re,
            "cashflow": cf,
            "equation_ok": round(bs["assets"], 2) == round(bs["liabilities_and_equity"], 2),
        }
