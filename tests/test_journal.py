from ai.rule_based_engine import RuleBasedJournalEngine


def test_rule_based_ad_keyword_maps_to_ad_expense():
    engine = RuleBasedJournalEngine("config/rules.json")
    tx = {
        "vendor": "메타",
        "description": "인스타 광고비",
        "memo": "",
        "amount": 100000,
        "payment_method": "보통예금",
    }
    result = engine.suggest(tx)
    assert result["debit_account"] == "광고선전비"
    assert result["credit_account"] == "보통예금"
    assert result["status"] in {"suggested", "review_needed"}


def test_unknown_keyword_returns_review_needed():
    engine = RuleBasedJournalEngine("config/rules.json")
    tx = {
        "vendor": "무명업체",
        "description": "기타잡비",
        "memo": "",
        "amount": 10000,
        "payment_method": "보통예금",
    }
    result = engine.suggest(tx)
    assert result["debit_account"] == "검토필요"
    assert result["status"] == "review_needed"


def test_unknown_keyword_with_unpaid_method_maps_to_accounts_payable():
    engine = RuleBasedJournalEngine("config/rules.json")
    tx = {
        "vendor": "무명업체",
        "description": "기타잡비",
        "memo": "",
        "amount": 10000,
        "payment_method": "미지급",
    }
    result = engine.suggest(tx)
    assert result["debit_account"] == "검토필요"
    assert result["credit_account"] == "미지급금"
    assert result["status"] == "review_needed"
