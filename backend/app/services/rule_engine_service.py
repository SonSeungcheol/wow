import json
from pathlib import Path
from datetime import date


class RuleEngineService:
    def __init__(self, rules_path: str):
        self.rules = json.loads(Path(rules_path).read_text(encoding="utf-8"))

    def suggest_accounts(self, description_text: str, payment_method: str, target_date: date) -> tuple[str, str, str]:
        text = description_text.lower()
        valid = [r for r in self.rules if r["effective_from"] <= str(target_date)]
        valid.sort(key=lambda r: r["effective_from"], reverse=True)
        for rule in valid:
            if any(k.lower() in text for k in rule["keywords"]):
                credit = "미지급금" if payment_method in ("외상", "미지급") and rule["credit_default"] == "보통예금" else rule["credit_default"]
                return rule["debit"], credit, rule["version"]
        return "검토필요", ("미지급금" if payment_method in ("외상", "미지급") else "보통예금"), "manual"
