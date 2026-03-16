# 한국 소규모 법인 회계·결산·법인세 신고 보조 웹앱

본 프로젝트는 거래 입력부터 결산/세무조정/신고보조서류 Excel 생성까지 지원하는 FastAPI + React 기반 실사용형 1차 완성본입니다.

## 1. 전체 설계 요약
- **엔진 분리**
  - 회계 엔진: 거래→분개 제안/승인/장부 생성
  - 결산 엔진: 결산조정 입력→결산분개 반영
  - 세무조정 엔진: 조정 입력/집계
  - 출력 엔진: 법인세 신고 보조 패키지 Excel 생성
- **규칙 분리**: `backend/app/rules/*.json` (버전 파일 포함)
- **DB 전략**: PostgreSQL 기본, SQLite 개발 허용
- **보안**: 관리자 로그인 + bcrypt 해시 + JWT

## 2. 폴더 구조
```
backend/
  app/
    api/
    core/
    db/
    models/
    schemas/
    services/
    rules/
    tests/
  alembic/
frontend/
docker-compose.yml
.env.example
README.md
```

## 3. 데이터 모델
- users, roles
- companies, fiscal_years, accounts
- transactions, journal_entries, journal_entry_lines
- closing_entries, closing_entry_lines
- tax_adjustments, tax_adjustment_lines
- export_jobs, audit_logs
- 공통 필드: created_at, updated_at, created_by

## 4. 회계 흐름
거래 입력 → 규칙 기반 분개 제안 → 사용자 승인 → 승인분개만 장부 반영 → 결산조정 반영 → 재무제표 생성(손익/재무상태/이익잉여금처분/현금흐름) → 세무조정 집계 → 신고용 Excel 출력

## 5. 주요 API
- 인증: `POST /api/auth/login`
- 대시보드: `GET /api/dashboard`
- 회사/회계기간/계정: `POST/GET /api/companies`, `POST/GET /api/fiscal-years`, `POST/GET /api/accounts`
- 거래/분개: `POST/GET /api/transactions`, `GET /api/journals/review`, `POST /api/journals/approve`
- 장부: `GET /api/ledgers/journal`, `GET /api/ledgers/general-ledger`, `GET /api/ledgers/trial-balance`
- 결산: `POST/GET /api/closing-entries`
- 재무제표: `GET /api/statements`
- 세무조정: `POST/GET /api/tax-adjustments`, `GET /api/tax-adjustments/summary`
- 규칙/감사로그: `GET /api/rules`, `GET /api/audit-logs`
- 출력: `GET /api/exports/excel`

## 6. 규칙 버전 관리
- `backend/app/rules/account_rules.json`
- `backend/app/rules/tax_rules.json`
- `backend/app/rules/vat_rules.json`
- `backend/app/rules/account_rules_v1.json`
- `backend/app/rules/tax_rules_v1.json`
- `backend/app/rules/vat_rules_v1.json`

## 7. 실행 방법
### Docker (권장)
```bash
docker-compose up --build
```
- Backend Swagger: http://localhost:8000/docs
- Frontend: http://localhost:5173

### 로컬(개발)
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

cd ../frontend
npm install
npm run dev
```

기본 관리자 계정(자동 생성):
- `admin / admin1234`

## 8. 테스트 방법
```bash
cd backend
pytest -q
```

테스트 범위:
- 분개 밸런스/승인
- 시산표/손익/재무상태표
- 결산분개
- 세무조정 집계
- export bytes 생성
- API(헬스/거래 입력)
