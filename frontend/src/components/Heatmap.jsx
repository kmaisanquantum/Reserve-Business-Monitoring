import { useState } from 'react';
import { MapPin } from 'lucide-react';

function riskColor(v, t) {
  const r = t > 0 ? v / t : 0;
  if (r > 0.35) return '#EF4444';
  if (r > 0.25) return '#F59E0B';
  if (r > 0.15) return '#3B82F6';
  return '#10B981';
}

export default function Heatmap({ provinces, loading }) {
  const [selected, setSelected] = useState(null);
  const [filter, setFilter]     = useState('all');

  const data = !provinces ? [] :
    filter === 'high' ? provinces.filter(p => p.total > 0 && p.violations / p.total > 0.25) :
    provinces;

  const sel = selected && provinces ? provinces.find(p => p.id === selected) : null;

  return (
    <div style={s.panel}>
      {/* Header */}
      <div style={s.header}>
        <div style={s.titleRow}>
          <div style={s.icon}><MapPin size={14} color="#F59E0B" /></div>
          <div>
            <div style={s.title}>Encroachment Heatmap</div>
            <div style={s.sub}>Foreign businesses in Reserved Activity sectors</div>
          </div>
        </div>
        <div style={s.filters}>
          {['all','high risk'].map(f => (
            <button key={f} style={{ ...s.filterBtn, ...(filter === f.split(' ')[0] ? s.filterActive : {}) }}
              onClick={() => setFilter(f.split(' ')[0])}>
              {f}
            </button>
          ))}
        </div>
      </div>

      {/* SVG map */}
      <div style={s.mapWrap}>
        {loading ? (
          <div style={s.loader}>Loading provinces…</div>
        ) : (
          <svg width="100%" height="100%" viewBox="80 50 460 240">
            {/* Grid */}
            {[0,1,2,3,4,5].map(i => (
              <line key={`v${i}`} x1={80+i*80} y1={50} x2={80+i*80} y2={290}
                stroke="#1E293B" strokeWidth={0.5} strokeDasharray="3 5"/>
            ))}
            {[0,1,2,3].map(i => (
              <line key={`h${i}`} x1={80} y1={50+i*65} x2={540} y2={50+i*65}
                stroke="#1E293B" strokeWidth={0.5} strokeDasharray="3 5"/>
            ))}

            {data.map(p => {
              const col  = riskColor(p.violations, p.total);
              const r    = 10 + Math.min(p.total / 180, 1) * 14;
              const isSel= selected === p.id;
              return (
                <g key={p.id} style={{ cursor:'pointer' }} onClick={() => setSelected(isSel ? null : p.id)}>
                  <circle cx={p.x} cy={p.y} r={r+8} fill={col} opacity={0.06}/>
                  <circle cx={p.x} cy={p.y} r={r}   fill={col}
                    opacity={isSel ? 0.92 : 0.6}
                    stroke={isSel ? '#F1F5F9' : col}
                    strokeWidth={isSel ? 2 : 0.5}/>
                  <text x={p.x} y={p.y} textAnchor="middle" dominantBaseline="central"
                    fontSize={r > 16 ? 9 : 7} fill="white" fontWeight="600"
                    style={{ pointerEvents:'none', userSelect:'none' }}>
                    {p.violations}
                  </text>
                </g>
              );
            })}

            <text x={310} y={286} textAnchor="middle" fontSize={9} fill="#4B5563">
              Papua New Guinea — Province Encroachment Index (bubble size = total foreign entities)
            </text>
          </svg>
        )}

        {/* Legend */}
        <div style={s.legend}>
          {[['#EF4444','>35% RAL'],['#F59E0B','>25%'],['#3B82F6','>15%'],['#10B981','Low']].map(([c,l]) => (
            <div key={l} style={s.legRow}>
              <div style={{ ...s.legDot, background:c }}/>
              <span style={s.legLabel}>{l}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Selected detail */}
      {sel && (
        <div style={s.detail}>
          <div>
            <div style={s.detTitle}>{sel.name}</div>
            <div style={s.detSub}>{sel.violations} violations / {sel.total} foreign entities</div>
          </div>
          <span style={{
            ...s.badge,
            background: sel.total > 0 && sel.violations/sel.total > 0.3 ? '#EF444433' : '#F59E0B22',
            color:      sel.total > 0 && sel.violations/sel.total > 0.3 ? '#FCA5A5'   : '#FCD34D',
            border:     `1px solid ${sel.total > 0 && sel.violations/sel.total > 0.3 ? '#EF444455' : '#F59E0B44'}`,
          }}>
            {sel.total > 0 ? Math.round(sel.violations/sel.total*100) : 0}% violation rate
          </span>
        </div>
      )}
    </div>
  );
}

const s = {
  panel:      { background:'#1A2235', border:'1px solid #1E293B', borderRadius:12, padding:16 },
  header:     { display:'flex', alignItems:'flex-start', justifyContent:'space-between', marginBottom:12 },
  titleRow:   { display:'flex', alignItems:'center', gap:8 },
  icon:       { width:28, height:28, borderRadius:8, background:'#F59E0B22', display:'flex', alignItems:'center', justifyContent:'center', flexShrink:0 },
  title:      { fontSize:13, fontWeight:600, color:'#F1F5F9' },
  sub:        { fontSize:11, color:'#94A3B8', marginTop:1 },
  filters:    { display:'flex', gap:4 },
  filterBtn:  { fontSize:11, padding:'3px 10px', borderRadius:99, border:'1px solid #1E293B', background:'#111827', color:'#94A3B8', cursor:'pointer' },
  filterActive:{ background:'#F59E0B22', color:'#F59E0B', borderColor:'#F59E0B55' },
  mapWrap:    { position:'relative', height:280 },
  loader:     { display:'flex', alignItems:'center', justifyContent:'center', height:'100%', color:'#6B7280', fontSize:13 },
  legend:     { position:'absolute', right:0, bottom:20, display:'flex', flexDirection:'column', gap:4 },
  legRow:     { display:'flex', alignItems:'center', gap:5 },
  legDot:     { width:8, height:8, borderRadius:'50%' },
  legLabel:   { fontSize:10, color:'#94A3B8' },
  detail:     { background:'#111827', border:'1px solid #1E293B', borderRadius:8, padding:'10px 12px', display:'flex', alignItems:'center', justifyContent:'space-between', marginTop:8 },
  detTitle:   { fontSize:13, fontWeight:600, color:'#F1F5F9' },
  detSub:     { fontSize:11, color:'#94A3B8', marginTop:2 },
  badge:      { fontSize:11, padding:'3px 8px', borderRadius:5, fontWeight:500 },
};
