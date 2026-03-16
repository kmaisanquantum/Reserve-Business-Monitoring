import { useState, useCallback } from 'react';
import { Activity, TrendingUp, TrendingDown, Users, Minus } from 'lucide-react';
import { api } from '../services/api';
import { useApi } from '../hooks/useApi';

const CATS = ['all', 'Local Growth', 'Foreign Takeover', 'Skills Gap'];

const CAT_META = {
  'Local Growth':     { icon: TrendingUp,   color:'#10B981', bg:'#10B98122', border:'#10B98140', textColor:'#6EE7B7' },
  'Foreign Takeover': { icon: TrendingDown,  color:'#EF4444', bg:'#EF444422', border:'#EF444440', textColor:'#FCA5A5' },
  'Skills Gap':       { icon: Users,         color:'#F59E0B', bg:'#F59E0B22', border:'#F59E0B40', textColor:'#FCD34D' },
  'Uncategorised':    { icon: Minus,         color:'#6B7280', bg:'#1E293B',   border:'#334155',   textColor:'#94A3B8' },
};

export default function TrendFeed() {
  const [cat, setCat] = useState('all');

  const fetcher = useCallback(() => api.getTrends(cat), [cat]);
  const { data: items, loading } = useApi(fetcher, 120_000);

  const counts = {};
  if (items) {
    CATS.forEach(c => {
      counts[c] = c === 'all' ? items.length : items.filter(i => i.category === c).length;
    });
  }

  return (
    <div style={s.panel}>
      <div style={s.header}>
        <div style={s.iconBox}><Activity size={14} color="#F59E0B" /></div>
        <div>
          <div style={s.title}>Trend Analyzer</div>
          <div style={s.sub}>Real-time NLP feed — PNG Business News + Gazette</div>
        </div>
      </div>

      {/* Filter pills */}
      <div style={s.pills}>
        {CATS.map(c => (
          <button key={c} style={{ ...s.pill, ...(cat === c ? s.pillActive : {}) }}
            onClick={() => setCat(c)}>
            {c}
            {items && (
              <span style={s.count}>{counts[c] ?? 0}</span>
            )}
          </button>
        ))}
      </div>

      {/* Feed */}
      <div style={s.feed}>
        {loading ? (
          <div style={s.loader}>Loading feed…</div>
        ) : !items?.length ? (
          <div style={s.loader}>No items found.</div>
        ) : (
          items.map((item, i) => {
            const meta = CAT_META[item.category] || CAT_META['Uncategorised'];
            const Icon = meta.icon;
            return (
              <div key={i} style={s.item}>
                <Icon size={13} color={meta.color} style={{ flexShrink:0, marginTop:1 }} />
                <div style={s.itemBody}>
                  <div style={s.headline}>{item.headline}</div>
                  <div style={s.meta}>
                    <span style={{ ...s.badge, background:meta.bg, color:meta.textColor, border:`1px solid ${meta.border}` }}>
                      {item.category}
                    </span>
                    <span style={s.metaText}>{item.source} · {item.time_ago}</span>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}

const s = {
  panel:    { background:'#1A2235', border:'1px solid #1E293B', borderRadius:12, padding:16 },
  header:   { display:'flex', alignItems:'center', gap:8, marginBottom:12 },
  iconBox:  { width:28, height:28, borderRadius:8, background:'#F59E0B22', display:'flex', alignItems:'center', justifyContent:'center', flexShrink:0 },
  title:    { fontSize:13, fontWeight:600, color:'#F1F5F9' },
  sub:      { fontSize:11, color:'#94A3B8' },
  pills:    { display:'flex', gap:6, marginBottom:10, flexWrap:'wrap' },
  pill:     { fontSize:11, padding:'3px 10px', borderRadius:99, border:'1px solid #1E293B', background:'#111827', color:'#94A3B8', cursor:'pointer', display:'flex', alignItems:'center', gap:5 },
  pillActive:{ background:'#F59E0B22', color:'#F59E0B', borderColor:'#F59E0B55' },
  count:    { background:'#1E293B', color:'#6B7280', borderRadius:99, padding:'0 5px', fontSize:10 },
  feed:     { maxHeight:280, overflowY:'auto', display:'flex', flexDirection:'column', gap:6 },
  loader:   { textAlign:'center', color:'#6B7280', fontSize:13, padding:'32px 0' },
  item:     { background:'#111827', border:'1px solid #1E293B', borderRadius:8, padding:'10px 12px', display:'flex', gap:10 },
  itemBody: { flex:1, minWidth:0 },
  headline: { fontSize:12, lineHeight:1.45, color:'#F1F5F9', marginBottom:5 },
  meta:     { display:'flex', alignItems:'center', gap:6 },
  badge:    { fontSize:10, padding:'1px 7px', borderRadius:4, fontWeight:500 },
  metaText: { fontSize:10, color:'#6B7280' },
};
