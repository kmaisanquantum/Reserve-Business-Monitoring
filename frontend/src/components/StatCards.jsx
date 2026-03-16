import { Globe, ShieldAlert, Network, Building2, ArrowUpRight, ArrowDownRight, Minus } from 'lucide-react';

const CARDS = [
  { key:'foreign_entities',  label:'Foreign Entities',       icon:Globe,       accent:'#3B82F6', deltaKey:'foreign_delta_pct'  },
  { key:'ral_violations',    label:'RAL Violations (month)', icon:ShieldAlert, accent:'#EF4444', deltaKey:'ral_delta_pct'      },
  { key:'fronting_clusters', label:'Fronting Clusters',      icon:Network,     accent:'#F59E0B', deltaKey:'fronting_delta_pct' },
  { key:'local_businesses',  label:'Local Businesses',       icon:Building2,   accent:'#10B981', deltaKey:'local_delta_pct'    },
];

function DeltaBadge({ value }) {
  if (value === 0) return <span style={{ fontSize:11, color:'#6B7280', display:'flex', alignItems:'center', gap:2 }}><Minus size={10}/>0%</span>;
  const up = value > 0;
  return (
    <span style={{ fontSize:11, color: up ? '#EF4444' : '#10B981', display:'flex', alignItems:'center', gap:2 }}>
      {up ? <ArrowUpRight size={10}/> : <ArrowDownRight size={10}/>}
      {Math.abs(value)}% vs last month
    </span>
  );
}

export default function StatCards({ stats, loading }) {
  return (
    <div style={styles.grid}>
      {CARDS.map(({ key, label, icon: Icon, accent, deltaKey }) => (
        <div key={key} style={styles.card}>
          <div style={styles.top}>
            <span style={styles.label}>{label}</span>
            <div style={{ ...styles.iconBox, background: accent + '22' }}>
              <Icon size={14} color={accent} />
            </div>
          </div>
          <div style={{ ...styles.value, color: loading ? '#334155' : '#F1F5F9' }}>
            {loading ? '—' : (stats?.[key] ?? 0).toLocaleString()}
          </div>
          {!loading && stats && <DeltaBadge value={stats[deltaKey] ?? 0} />}
        </div>
      ))}
    </div>
  );
}

const styles = {
  grid:    { display:'grid', gridTemplateColumns:'repeat(4,1fr)', gap:12, padding:'16px 24px 0' },
  card:    { background:'#1A2235', border:'1px solid #1E293B', borderRadius:12, padding:'14px 16px', display:'flex', flexDirection:'column', gap:6 },
  top:     { display:'flex', alignItems:'center', justifyContent:'space-between' },
  label:   { fontSize:11, fontWeight:500, color:'#94A3B8' },
  iconBox: { width:26, height:26, borderRadius:7, display:'flex', alignItems:'center', justifyContent:'center' },
  value:   { fontSize:24, fontWeight:700, lineHeight:1 },
};
