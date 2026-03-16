import React, { useState } from 'react'
import { createRoot } from 'react-dom/client'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

type Tx = {
  company_id:number; fiscal_year_id:number; date:string; vendor:string; description:string; amount:number;
  vat_included:boolean; supply_amount:number; vat_amount:number; payment_method:string; evidence_type:string; memo:string;
}

function App(){
  const [token,setToken]=useState('')
  const [msg,setMsg]=useState('')
  const [tx,setTx]=useState<Tx>({company_id:1,fiscal_year_id:1,date:'2026-01-01',vendor:'',description:'',amount:0,vat_included:true,supply_amount:0,vat_amount:0,payment_method:'보통예금',evidence_type:'세금계산서',memo:''})

  const call = async(path:string, method='GET', body?:unknown)=>{
    const res = await fetch(`${API}${path}`, {method, headers:{'Content-Type':'application/json', ...(token?{Authorization:`Bearer ${token}`}:{})}, body: body?JSON.stringify(body):undefined})
    const text = await res.text();
    if(!res.ok) throw new Error(text)
    return text ? JSON.parse(text) : {}
  }

  return <div style={{fontFamily:'sans-serif',padding:20}}>
    <h2>한국 소규모 법인 결산/법인세 보조 웹앱</h2>
    <button onClick={async()=>{const r=await call('/auth/login','POST',{username:'admin',password:'admin1234'}); setToken(r.access_token);setMsg('로그인 성공')}}>기본 로그인(admin)</button>
    <button onClick={async()=>{await call('/companies','POST',{name:'샘플법인',business_number:'123-45-67890'});setMsg('회사 생성')}}>회사등록</button>
    <button onClick={async()=>{await call('/fiscal-years','POST',{company_id:1,start_date:'2026-01-01',end_date:'2026-12-31'});setMsg('회계기간 생성')}}>회계기간 생성</button>
    <button onClick={async()=>{
      const accts=[['101','보통예금','자산'],['201','미지급금','부채'],['202','가수금','부채'],['401','매출','수익'],['501','광고선전비','비용'],['502','운반비','비용'],['503','지급수수료','비용'],['150','원재료','자산'],['504','복리후생비','비용'],['999','검토필요','비용'],['505','감가상각비','비용'],['109','감가상각누계액','자산'],['110','선급비용','자산'],['111','미수수익','자산'],['210','선수수익','부채'],['506','매출원가','비용']]
      for(const a of accts){await call('/accounts','POST',{company_id:1,code:a[0],name:a[1],type:a[2]})}
      setMsg('기초 계정 생성')
    }}>기초계정 생성</button>
    <hr/>
    <h3>거래 입력</h3>
    <input placeholder='거래처' value={tx.vendor} onChange={e=>setTx({...tx,vendor:e.target.value})}/>
    <input placeholder='적요' value={tx.description} onChange={e=>setTx({...tx,description:e.target.value})}/>
    <input type='number' placeholder='금액' value={tx.amount} onChange={e=>setTx({...tx,amount:Number(e.target.value)})}/>
    <button onClick={async()=>{await call('/transactions','POST',tx);setMsg('거래+분개제안 완료')}}>저장</button>
    <button onClick={async()=>{const r=await call('/statements?company_id=1&fiscal_year_id=1');setMsg(JSON.stringify(r))}}>재무제표 조회</button>
    <button onClick={()=>window.open(`${API}/exports/excel?company_id=1&fiscal_year_id=1`,'_blank')}>Excel 다운로드</button>
    <pre style={{whiteSpace:'pre-wrap'}}>{msg}</pre>
  </div>
}

createRoot(document.getElementById('root')!).render(<App />)
