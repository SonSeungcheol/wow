from app.services.ledger_service import LedgerService


class StatementService:
    @staticmethod
    def income_statement(tb: dict):
        revenue = sum(v["credit"] - v["debit"] for v in tb.values() if v["type"] == "수익")
        expense = sum(v["debit"] - v["credit"] for v in tb.values() if v["type"] == "비용")
        net_income = revenue - expense
        return {"revenue": revenue, "expense": expense, "net_income": net_income}

    @staticmethod
    def balance_sheet(tb: dict, net_income: float):
        assets = sum(v["debit"] - v["credit"] for v in tb.values() if v["type"] == "자산")
        liabilities = sum(v["credit"] - v["debit"] for v in tb.values() if v["type"] == "부채")
        equity = sum(v["credit"] - v["debit"] for v in tb.values() if v["type"] == "자본") + net_income
        return {"assets": assets, "liabilities": liabilities, "equity": equity, "liabilities_and_equity": liabilities + equity}

    @staticmethod
    def retained_earnings_statement(net_income: float):
        return {"beginning": 0.0, "net_income": net_income, "ending": net_income}

    @staticmethod
    def cashflow_indirect(tb: dict, net_income: float):
        delta_receivables = sum(v["debit"] - v["credit"] for k, v in tb.items() if "미수" in k)
        delta_payables = sum(v["credit"] - v["debit"] for k, v in tb.items() if "미지급" in k)
        operating = net_income - delta_receivables + delta_payables
        return {"operating_cashflow": operating, "investing_cashflow": 0.0, "financing_cashflow": 0.0, "net_change": operating}

    @staticmethod
    def statements(db, company_id: int, fiscal_year_id: int):
        tb = LedgerService.trial_balance(db, company_id, fiscal_year_id)
        pl = StatementService.income_statement(tb)
        bs = StatementService.balance_sheet(tb, pl["net_income"])
        re = StatementService.retained_earnings_statement(pl["net_income"])
        cf = StatementService.cashflow_indirect(tb, pl["net_income"])
        return {"trial_balance": tb, "income_statement": pl, "balance_sheet": bs, "retained_earnings": re, "cashflow": cf}
