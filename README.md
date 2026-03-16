# 한국 소규모 법인 회계·결산·법인세 신고 보조 웹앱

FastAPI + React 기반으로 거래 입력부터 분개, 장부, 결산조정, 재무제표, 세무조정, 신고 보조 Excel 내보내기까지 지원합니다.

## 1) 전체 설계
- 백엔드: FastAPI + SQLAlchemy + Alembic
- 프론트엔드: React + TypeScript + Vite
- DB: PostgreSQL(기본), SQLite(개발)
- 출력: Excel(openpyxl/pandas)
- 규칙 버전 관리: `backend/app/rules/*.json` + `effective_from`

## 2) 폴더 구조
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
```

## 3) 주요 회계 흐름
거래입력 -> 규칙기반 분개 제안 -> 승인 -> 분개장/원장/시산표 -> 결산조정 분개 반영 -> 재무제표 -> 세무조정 집계 -> Excel 출력

## 4) 로컬 실행 (SQLite 개발)
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```
프론트:
```bash
cd frontend
npm install
npm run dev
```
기본 로그인 계정: `admin / admin1234`

## 5) Docker 실행 (PostgreSQL)
```bash
docker-compose up --build
```
- Backend: http://localhost:8000/docs
- Frontend: http://localhost:5173

## 6) 테스트
```bash
cd backend
pytest -q
```

## 7) API 요약
- 인증: `/api/auth/login`
- 회사/회계기간/계정: `/api/companies`, `/api/fiscal-years`, `/api/accounts`
- 거래/분개: `/api/transactions`, `/api/journals`, `/api/journals/approve`
- 장부/재무제표: `/api/ledgers/trial-balance`, `/api/statements`
- 결산: `/api/closing-entries`
- 세무조정: `/api/tax-adjustments`, `/api/tax-adjustments/summary`
- 내보내기: `/api/exports/excel`
