import React, { useMemo, useState } from 'react'
import { createRoot } from 'react-dom/client'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

function App() {
  const [token, setToken] = useState('')
  const [menu, setMenu] = useState('대시보드')
  const [companyId] = useState(1)
  const [fiscalYearId] = useState(1)
  const [output, setOutput] = useState('')
  const [tx, setTx] = useState({ date: '2026-01-02', vendor: '', description: '', amount: 0, vat_included: true, supply_amount: 0, vat_amount: 0, payment_method: '보통예금', evidence_type: '세금계산서', memo: '' })

  const menus = useMemo(() => ['로그인', '대시보드', '회사설정', '회계기간', '계정과목', '거래입력', '분개검토', '분개장', '총계정원장', '합계잔액시산표', '결산조정', '재무제표', '세무조정', '신고자료 출력', '규칙관리', '감사로그'], [])

  const call = async (path: string, method = 'GET', body?: unknown) => {
    const res = await fetch(`${API}${path}`, {
      method,
      headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) },
      body: body ? JSON.stringify(body) : undefined,
    })
    const text = await res.text()
    if (!res.ok) throw new Error(text)
    return text ? JSON.parse(text) : {}
  }

  const seedAccounts = async () => {
    const rows = [['101', '보통예금', '자산'], ['201', '미지급금', '부채'], ['202', '가수금', '부채'], ['203', '선수수익', '부채'], ['108', '미수수익', '자산'], ['109', '감가상각누계액', '자산'], ['110', '선급비용', '자산'], ['120', '가지급금', '자산'], ['150', '원재료', '자산'], ['301', '자본금', '자본'], ['401', '매출', '수익'], ['501', '광고선전비', '비용'], ['502', '운반비', '비용'], ['503', '지급수수료', '비용'], ['504', '복리후생비', '비용'], ['505', '감가상각비', '비용'], ['506', '매출원가', '비용'], ['999', '검토필요', '비용']]
    for (const r of rows) await call('/accounts', 'POST', { company_id: companyId, code: r[0], name: r[1], type: r[2] })
    setOutput('계정과목 초기 등록 완료')
  }

  const renderPanel = () => {
    if (menu === '로그인') return <button onClick={async () => { const r = await call('/auth/login', 'POST', { username: 'admin', password: 'admin1234' }); setToken(r.access_token); setOutput('로그인 성공') }}>관리자 로그인</button>
    if (menu === '대시보드') return <button onClick={async () => setOutput(JSON.stringify(await call(`/dashboard?company_id=${companyId}&fiscal_year_id=${fiscalYearId}`), null, 2))}>조회</button>
    if (menu === '회사설정') return <button onClick={async () => { await call('/companies', 'POST', { name: '샘플법인', business_number: '123-45-67890', corporation_number: '110111-1234567', representative_name: '홍길동', business_type: '도소매', address: '서울시 강남구' }); setOutput('회사 등록 완료') }}>회사 등록</button>
    if (menu === '회계기간') return <button onClick={async () => { await call('/fiscal-years', 'POST', { company_id: companyId, start_date: '2026-01-01', end_date: '2026-12-31' }); setOutput('회계기간 등록 완료') }}>회계기간 등록</button>
    if (menu === '계정과목') return <button onClick={seedAccounts}>기초계정 자동 등록</button>
    if (menu === '거래입력') return <div>
      <input placeholder='거래처' value={tx.vendor} onChange={e => setTx({ ...tx, vendor: e.target.value })} />
      <input placeholder='적요' value={tx.description} onChange={e => setTx({ ...tx, description: e.target.value })} />
      <input type='number' placeholder='금액' value={tx.amount} onChange={e => setTx({ ...tx, amount: Number(e.target.value), supply_amount: Math.round(Number(e.target.value) / 1.1), vat_amount: Number(e.target.value) - Math.round(Number(e.target.value) / 1.1) })} />
      <button onClick={async () => { await call('/transactions', 'POST', { company_id: companyId, fiscal_year_id: fiscalYearId, ...tx }); setOutput('거래 저장 및 분개 제안 완료') }}>저장</button>
    </div>
    if (menu === '분개검토') return <button onClick={async () => setOutput(JSON.stringify(await call(`/journals/review?company_id=${companyId}&fiscal_year_id=${fiscalYearId}`), null, 2))}>미승인 분개 조회</button>
    if (menu === '분개장') return <button onClick={async () => setOutput(JSON.stringify(await call(`/ledgers/journal?company_id=${companyId}&fiscal_year_id=${fiscalYearId}`), null, 2))}>조회</button>
    if (menu === '총계정원장') return <button onClick={async () => setOutput(JSON.stringify(await call(`/ledgers/general-ledger?company_id=${companyId}&fiscal_year_id=${fiscalYearId}`), null, 2))}>조회</button>
    if (menu === '합계잔액시산표') return <button onClick={async () => setOutput(JSON.stringify(await call(`/ledgers/trial-balance?company_id=${companyId}&fiscal_year_id=${fiscalYearId}`), null, 2))}>조회</button>
    if (menu === '결산조정') return <button onClick={async () => { await call('/closing-entries', 'POST', { company_id: companyId, fiscal_year_id: fiscalYearId, adjustment_type: '감가상각', amount: 10000, description: '연말 감가상각' }); setOutput('결산조정 입력 완료') }}>감가상각 조정 등록</button>
    if (menu === '재무제표') return <button onClick={async () => setOutput(JSON.stringify(await call(`/statements?company_id=${companyId}&fiscal_year_id=${fiscalYearId}`), null, 2))}>조회</button>
    if (menu === '세무조정') return <button onClick={async () => { await call('/tax-adjustments', 'POST', { company_id: companyId, fiscal_year_id: fiscalYearId, category: '손금불산입', reserve_type: '유보', description: '접대비 한도초과', amount: 50000 }); setOutput(JSON.stringify(await call(`/tax-adjustments/summary?company_id=${companyId}&fiscal_year_id=${fiscalYearId}`), null, 2)) }}>세무조정 입력+집계</button>
    if (menu === '신고자료 출력') return <button onClick={() => window.open(`${API}/exports/excel?company_id=${companyId}&fiscal_year_id=${fiscalYearId}`, '_blank')}>Excel 다운로드</button>
    if (menu === '규칙관리') return <button onClick={async () => setOutput(JSON.stringify(await call('/rules'), null, 2))}>규칙 버전 조회</button>
    if (menu === '감사로그') return <button onClick={async () => setOutput(JSON.stringify(await call('/audit-logs'), null, 2))}>감사로그 조회</button>
    return null
  }

  return <div style={{ fontFamily: 'sans-serif', padding: 16 }}>
    <h2>한국 소규모 법인 결산 및 법인세 신고 보조</h2>
    <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>{menus.map(m => <button key={m} onClick={() => setMenu(m)} style={{ background: menu === m ? '#ddd' : '#fff' }}>{m}</button>)}</div>
    <h3>{menu}</h3>
    {renderPanel()}
    <pre style={{ whiteSpace: 'pre-wrap', background: '#f7f7f7', padding: 12, minHeight: 180 }}>{output}</pre>
  </div>
}

createRoot(document.getElementById('root')!).render(<App />)
