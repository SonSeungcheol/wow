import json
from datetime import date
from pathlib import Path


class RuleEngineService:
    def __init__(self, rules_path: str):
        self.rules = json.loads(Path(rules_path).read_text(encoding="utf-8"))

    def suggest(self, text: str, payment_method: str, target_date: date) -> dict:
        joined = text.lower()
        valid = [r for r in self.rules if r["effective_from"] <= str(target_date)]
        valid.sort(key=lambda r: r["effective_from"], reverse=True)
        for rule in valid:
            if any(k.lower() in joined for k in rule["keywords"]):
                credit = "미지급금" if payment_method in ("외상", "미지급") and rule["credit_default"] == "보통예금" else rule["credit_default"]
                return {
                    "debit_account": rule["debit"],
                    "credit_account": credit,
                    "explanation": rule.get("explanation", "규칙 매칭"),
                    "review_points": "\n".join(rule.get("review_points", [])),
                    "confidence": float(rule.get("confidence", 0.7)),
                    "rule_version": rule.get("version", "v1"),
                }
        return {
            "debit_account": "검토필요",
            "credit_account": "미지급금" if payment_method in ("외상", "미지급") else "보통예금",
            "explanation": "일치하는 분개 규칙이 없어 검토 필요",
            "review_points": "증빙 검토 후 계정과목 지정",
            "confidence": 0.3,
            "rule_version": "manual",
        }
