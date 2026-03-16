"""Rule-based journal suggestion engine."""
from __future__ import annotations

import json
from pathlib import Path

from ai.ai_engine import BaseJournalEngine


class RuleBasedJournalEngine(BaseJournalEngine):
    def __init__(self, rules_path: str):
        self.rules = json.loads(Path(rules_path).read_text(encoding="utf-8"))

    def suggest(self, transaction: dict) -> dict:
        text = f"{transaction.get('vendor', '')} {transaction.get('description', '')} {transaction.get('memo', '')}".lower()
        payment_method = transaction.get("payment_method", "")

        for rule in self.rules:
            if any(keyword.lower() in text for keyword in rule["keywords"]):
                credit_account = rule["credit_account"]
                if credit_account == "보통예금" and payment_method in ("외상", "미지급"):
                    credit_account = "미지급금"
                explanation = f"키워드({rule['name']}) 매칭으로 분개를 제안했습니다."
                status = "review_needed" if rule.get("confidence", 0) < 0.8 else "suggested"
                return {
                    "debit_account": rule["debit_account"],
                    "credit_account": credit_account,
                    "amount": float(transaction["amount"]),
                    "explanation": explanation,
                    "review_points": "\n".join(rule.get("review_points", ["증빙 확인 필요"])),
                    "status": status,
                }

        return {
            "debit_account": "검토필요",
            "credit_account": "미지급금" if payment_method in ("외상", "미지급") else "보통예금",
            "amount": float(transaction["amount"]),
            "explanation": "일치하는 규칙이 없어 수동 검토가 필요합니다.",
            "review_points": "거래 성격 확인 후 계정과목 수동 지정",
            "status": "review_needed",
        }
