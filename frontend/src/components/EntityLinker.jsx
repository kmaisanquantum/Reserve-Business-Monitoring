import { useState } from 'react';
import { Network, AlertTriangle, ChevronRight, Building2, Zap } from 'lucide-react';

export default function EntityLinker({ clusters, loading }) {
  const [expanded, setExpanded] = useState(null);

  return (
    <div style={s.panel}>
      <div style={s.header}>
        <div style={s.iconBox}><Network size={14} color="#F59E0B" /></div>
        <div>
          <div style={s.title}>Entity Linker</div>
          <div style={s.sub}>Simulated annealing — fronting cluster analysis</div>
        </div>
      </div>

      {loading ? (
        <div style={s.loader}>Analysing ownership patterns…</div>
      ) : !clusters?.length ? (
        <div style={s.loader}>No fronting clusters detected.</div>
      ) : (
        <div style={s.list}>
          {clusters.map((c, i) => {
            const isExp  = expanded === i;
            const hiRisk = c.risk_score > 50;
            return (
              <div key={i} style={{ ...s.cluster, borderColor: isExp ? '#EF444466' : '#1E293B' }}
                onClick={() => setExpanded(isExp ? null : i)}>

                {/* Row */}
                <div style={{ ...s.row, background: isExp ? '#EF444411' : '#111827' }}>
                  <div style={{ ...s.cIcon, background: hiRisk ? '#EF444433' : '#F59E0B33' }}>
                    <AlertTriangle size={13} color={hiRisk ? '#EF4444' : '#F59E0B'} />
                  </div>
                  <div style={s.rowBody}>
                    <div style={s.companyName}>{c.companies?.[0]}</div>
                    <div style={s.trigger}>
                      {c.trigger === 'shared_director' ? 'Shared director' : 'Shared address'}: {c.shared_value}
                    </div>
                  </div>
                  <div style={s.rowRight}>
                    <span style={{ ...s.badge, ...(hiRisk ? s.badgeDanger : s.badgeWarn) }}>
                      Risk {c.risk_score}
                    </span>
                    <ChevronRight size={13} color="#6B7280"
                      style={{ transform: isExp ? 'rotate(90deg)' : 'none', transition:'0.2s' }} />
                  </div>
                </div>

                {/* Expanded */}
                {isExp && (
                  <div style={s.detail}>
                    <div style={s.detGrid}>
                      <div>
                        <div style={s.detLabel}>LINKED COMPANIES ({c.companies?.length})</div>
                        {c.companies?.map((name, j) => (
                          <div key={j} style={s.detRow}>
                            <Building2 size={10} color="#6B7280" />
                            <span style={s.detText}>{name}</span>
                          </div>
                        ))}
                      </div>
                      <div>
                        <div style={s.detLabel}>RAL SECTORS</div>
                        {c.sectors?.map((sec, j) => (
                          <div key={j} style={{ marginBottom:4 }}>
                            <span style={{ ...s.badge, ...s.badgeDanger, fontSize:10 }}>{sec}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                    <div style={s.saRow}>
                      <Zap size={10} color="#F59E0B" />
                      <span style={s.saText}>
                        SA confidence: {c.sa_confidence}% — optimised from raw candidates
                      </span>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

const s = {
  panel:      { background:'#1A2235', border:'1px solid #1E293B', borderRadius:12, padding:16 },
  header:     { display:'flex', alignItems:'center', gap:8, marginBottom:12 },
  iconBox:    { width:28, height:28, borderRadius:8, background:'#F59E0B22', display:'flex', alignItems:'center', justifyContent:'center', flexShrink:0 },
  title:      { fontSize:13, fontWeight:600, color:'#F1F5F9' },
  sub:        { fontSize:11, color:'#94A3B8' },
  loader:     { textAlign:'center', color:'#6B7280', fontSize:13, padding:'32px 0' },
  list:       { display:'flex', flexDirection:'column', gap:6 },
  cluster:    { border:'1px solid #1E293B', borderRadius:8, overflow:'hidden', cursor:'pointer', transition:'border-color .15s' },
  row:        { padding:'10px 12px', display:'flex', alignItems:'center', gap:10 },
  cIcon:      { width:30, height:30, borderRadius:'50%', display:'flex', alignItems:'center', justifyContent:'center', flexShrink:0 },
  rowBody:    { flex:1, minWidth:0 },
  companyName:{ fontSize:12, fontWeight:500, color:'#F1F5F9', whiteSpace:'nowrap', overflow:'hidden', textOverflow:'ellipsis' },
  trigger:    { fontSize:11, color:'#94A3B8', marginTop:1, whiteSpace:'nowrap', overflow:'hidden', textOverflow:'ellipsis' },
  rowRight:   { display:'flex', alignItems:'center', gap:6, flexShrink:0 },
  badge:      { display:'inline-flex', alignItems:'center', padding:'2px 7px', borderRadius:5, fontSize:11, fontWeight:500 },
  badgeDanger:{ background:'#EF444422', color:'#FCA5A5', border:'1px solid #EF444440' },
  badgeWarn:  { background:'#F59E0B22', color:'#FCD34D', border:'1px solid #F59E0B40' },
  detail:     { padding:'10px 12px', borderTop:'1px solid #1E293B' },
  detGrid:    { display:'grid', gridTemplateColumns:'1fr 1fr', gap:12, marginBottom:10 },
  detLabel:   { fontSize:10, fontWeight:500, color:'#94A3B8', marginBottom:6, letterSpacing:'0.04em' },
  detRow:     { display:'flex', alignItems:'center', gap:5, marginBottom:3 },
  detText:    { fontSize:11, color:'#F1F5F9' },
  saRow:      { display:'flex', alignItems:'center', gap:5 },
  saText:     { fontSize:11, color:'#94A3B8' },
};
