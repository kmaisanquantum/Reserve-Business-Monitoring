import { useState, useCallback } from 'react';
import { Eye, RefreshCw, Search, X } from 'lucide-react';
import { api } from '../services/api';

export default function NavBar({ onRefreshAll, lastUpdated }) {
  const [refreshing, setRefreshing] = useState(false);
  const [query, setQuery]           = useState('');
  const [results, setResults]       = useState([]);

  const handleRefresh = useCallback(async () => {
    setRefreshing(true);
    try { await api.triggerScrape(); } catch (_) {}
    await onRefreshAll();
    setRefreshing(false);
  }, [onRefreshAll]);

  const handleSearch = useCallback(async (e) => {
    const q = e.target.value;
    setQuery(q);
    if (q.length < 2) { setResults([]); return; }
    try {
      const data = await api.search(q);
      setResults(data.slice(0, 8));
    } catch (_) {
      setResults([]);
    }
  }, []);

  return (
    <header style={styles.bar} className="nav-container">
      {/* Brand */}
      <div style={styles.brand} className="nav-brand">
        <div style={styles.logoBox}><Eye size={16} color="#F59E0B" /></div>
        <div>
          <div style={styles.title}>PNG Business Transparency Monitor</div>
          <div style={styles.sub}>IPA Registry · Gazette · NPC · Business News</div>
        </div>
      </div>

      {/* Search */}
      <div style={styles.searchWrap} className="nav-search">
        <Search size={13} color="#6B7280" style={styles.searchIcon} />
        <input
          style={styles.searchInput}
          placeholder="Search company name…"
          value={query}
          onChange={handleSearch}
        />
        {query && (
          <button style={styles.clearBtn} onClick={() => { setQuery(''); setResults([]); }}>
            <X size={12} color="#6B7280" />
          </button>
        )}
        {results.length > 0 && (
          <div style={styles.dropdown}>
            {results.map((r, i) => (
              <div key={i} style={styles.dropItem}>
                <span style={styles.dropName}>{r.company_name}</span>
                <div style={styles.dropMeta}>
                  {r.sector && <span style={styles.dropTag}>{r.sector}</span>}
                  {r.ral_violation && <span style={{ ...styles.dropTag, color: '#FCA5A5', background: '#EF444422' }}>RAL</span>}
                  {r.is_foreign    && <span style={{ ...styles.dropTag, color: '#FDBA74', background: '#F9730022' }}>Foreign</span>}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Right controls */}
      <div style={styles.right} className="nav-right">
        <div style={styles.liveDot}><span style={styles.dot} />Live</div>
        <span style={styles.updated}>{lastUpdated}</span>
        <button style={styles.refreshBtn} onClick={handleRefresh} disabled={refreshing}>
          <RefreshCw size={11} style={refreshing ? styles.spin : {}} />
          {refreshing ? 'Refreshing…' : 'Refresh'}
        </button>
      </div>
    </header>
  );
}

const styles = {
  bar:          { display:'flex', alignItems:'center', gap:16, padding:'12px var(--side-padding, 24px)', background:'#111827', borderBottom:'1px solid #1E293B', position:'sticky', top:0, zIndex:100, flexWrap: 'wrap' },
  brand:        { display:'flex', alignItems:'center', gap:10, flexShrink:0 },
  logoBox:      { width:32, height:32, borderRadius:8, background:'#F59E0B22', border:'1px solid #F59E0B44', display:'flex', alignItems:'center', justifyContent:'center' },
  title:        { fontSize:14, fontWeight:700, color:'#F1F5F9', lineHeight:1.2 },
  sub:          { fontSize:11, color:'#6B7280' },
  searchWrap:   { flex:1, maxWidth:360, position:'relative', minWidth: 200 },
  searchIcon:   { position:'absolute', left:10, top:'50%', transform:'translateY(-50%)', pointerEvents:'none' },
  searchInput:  { width:'100%', background:'#1A2235', border:'1px solid #1E293B', borderRadius:8, padding:'7px 32px 7px 32px', color:'#F1F5F9', fontSize:13, outline:'none' },
  clearBtn:     { position:'absolute', right:8, top:'50%', transform:'translateY(-50%)', background:'none', border:'none', cursor:'pointer', display:'flex' },
  dropdown:     { position:'absolute', top:'calc(100% + 6px)', left:0, right:0, background:'#1A2235', border:'1px solid #1E293B', borderRadius:10, overflow:'hidden', zIndex:200 },
  dropItem:     { padding:'9px 12px', borderBottom:'1px solid #1E293B', cursor:'pointer' },
  dropName:     { fontSize:12, color:'#F1F5F9', display:'block', marginBottom:3 },
  dropMeta:     { display:'flex', gap:4 },
  dropTag:      { fontSize:10, padding:'1px 6px', borderRadius:4, background:'#1E293B', color:'#94A3B8' },
  right:        { display:'flex', alignItems:'center', gap:12, flexShrink:0 },
  liveDot:      { display:'flex', alignItems:'center', gap:5, fontSize:12, color:'#6B7280' },
  dot:          { display:'inline-block', width:7, height:7, borderRadius:'50%', background:'#10B981' },
  updated:      { fontSize:11, color:'#6B7280' },
  refreshBtn:   { display:'flex', alignItems:'center', gap:5, fontSize:12, padding:'6px 12px', borderRadius:8, background:'#1A2235', color:'#94A3B8', border:'1px solid #1E293B', cursor:'pointer' },
  spin:         { animation:'spin 1s linear infinite' },
};
