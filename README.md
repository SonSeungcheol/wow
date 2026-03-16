# 소규모 한국 법인용 복식부기 회계 보조 MVP

사람이 입력한 거래내역을 기반으로 규칙 기반 분개를 제안하고, 승인된 분개로 분개장/총계정원장/시산표/손익계산서/재무상태표를 자동 생성하는 Streamlit 앱입니다.

## 주요 기능
- 거래 입력 (거래일자, 거래처, 적요, 금액, 결제수단, 부가세 포함 여부, 메모)
- 규칙 기반 분개 제안 (차변/대변 계정, 설명, 체크포인트, 검토 필요 상태)
- 분개 수정 및 승인 후 SQLite 저장
- 회계 산출물 조회
  - 분개장
  - 총계정원장
  - 시산표
  - 손익계산서
  - 재무상태표
- Excel 다운로드
- 설정 파일 기반 관리
  - 회사 정보(`config/settings.json`)
  - 계정과목(`config/accounts.json`)
  - 분개 규칙(`config/rules.json`)

## 폴더 구조
```
project_root/
  app.py
  requirements.txt
  README.md
  config/
    accounts.json
    rules.json
    settings.json
  core/
    db.py
    models.py
    journal.py
    ledger.py
    statements.py
    validators.py
  ai/
    ai_engine.py
    rule_based_engine.py
    openai_engine.py
  exports/
    excel_exporter.py
  tests/
    test_journal.py
    test_statements.py
```

## 설치 및 실행
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
streamlit run app.py
```

## 테스트
```bash
pytest -q
```

## 샘플 거래 입력 예시 (5개)
아래 키워드를 사용하면 규칙 기반 분개 제안이 동작합니다.
1. 거래처: 메타, 적요: 인스타 광고비
2. 거래처: CJ대한통운, 적요: 택배 배송비
3. 거래처: 포장나라, 적요: 포장재 구매
4. 거래처: 세무법인OO, 적요: 기장 수수료
5. 거래처: 대표님, 적요: 대표 대납 카드결제

## 주의사항
- 본 프로젝트는 한국 회계 실무 보조용 MVP입니다.
- 세무 신고 자동 제출 기능은 포함하지 않습니다.
- AI 분개 제안은 반드시 사람이 검토/승인해야 합니다.
