import React from 'react'
export default function MetricsBar({metrics}:{metrics:any}){
  if(!metrics) return null
  const keys = Object.keys(metrics)
  return (
    <div style={{display:'flex', gap:8, flexWrap:'wrap', marginTop:8}}>
      {keys.map(k => (
        <span key={k} style={{padding:'4px 8px', borderRadius:8, background:'#222', color:'#fff'}}>
          {k}: {Number(metrics[k]).toFixed(3)}
        </span>
      ))}
    </div>
  )
}