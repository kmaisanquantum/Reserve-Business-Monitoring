import { Bell, ShieldAlert, AlertTriangle, AlertCircle, CheckCircle2, Globe } from 'lucide-react';
import { api } from '../services/api';

const PRIO = {
  critical: { color:'#EF4444', bg:'#EF444422', border:'#EF444455', Icon:ShieldAlert  },
  high:     { color:'#F59E0B', bg:'#F59E0B22', border:'#F59E0B44', Icon:AlertTriangle },
  medium:   { color:'#3B82F6', bg:'#3B82F622', border:'#3B82F644', Icon:AlertCircle   },
  low:      { color:'#10B981', bg:'#10B98122', border:'#10B98144', Icon:CheckCircle2  },
};

export default function AlertPanel({ alerts, loading, onDismiss }) {
  const active = (alerts || []).filter(a => !a.dismissed);

  const handleDismiss = async (id) => {
    try { await api.dismissAlert(id); } catch (_) {}
    onDismiss(id);
  };

  return (
    <div style={s.panel}>
      <div style={s.header}>
        <div style={s.iconBox}><Bell size={14} color="#F59E0B" /></div>
        <div style={{ flex:1 }}>
          <div style={s.title}>Regulatory Alert System</div>
          <div style={s.sub}>FEC issued in Reserved Activity sectors</div>
        </div>
        {active.length > 0 && (
          <div style={s.badge}>{active.length}</div>
        )}
      </div>

      <div style={s.list}>
        {loading ? (
          <div style={s.loader}>Loading alerts…</div>
        ) : active.length === 0 ? (
          <div style={s.empty}>
            <CheckCircle2 size={22} color="#10B981" />
            <span style={s.emptyText}>No active alerts</span>
          </div>
        ) : (
          active.map(alert => {
            const prio = PRIO[alert.priority] || PRIO.medium;
            return (
              <div key={alert.id} style={{ ...s.alert, background:prio.bg, border:`1px solid ${prio.border}` }}>
                <prio.Icon size={15} color={prio.color} style={{ flexShrink:0, marginTop:1 }} />
                <div style={s.alertBody}>
                  <div style={s.alertTop}>
                    <span style={s.company}>{alert.company}</span>
                    <span style={{ ...s.tag, background:prio.bg, color:prio.color, border:`1px solid ${prio.border}` }}>
                      {alert.priority.toUpperCase()}
                    </span>
                    <span style={s.foreignTag}>
                      <Globe size={9}/> Foreign
                    </span>
                  </div>
                  <div style={s.alertDetail}>
                    FEC #{alert.cert_number} —{' '}
                    <span style={{ color:prio.color }}>{alert.sector}</span>{' '}
                    is a Reserved Activity
                  </div>
                  <div style={s.alertLoc}>{alert.province} · {alert.created_at ? new Date(alert.created_at).toLocaleDateString() : ''}</div>
                </div>
                <button style={s.dismissBtn} onClick={() => handleDismiss(alert.id)}>
                  Dismiss
                </button>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}

const s = {
  panel:      { background:'#1A2235', border:'1px solid #1E293B', borderRadius:12, padding:16 },
  header:     { display:'flex', alignItems:'center', gap:8, marginBottom:12 },
  iconBox:    { width:28, height:28, borderRadius:8, background:'#F59E0B22', display:'flex', alignItems:'center', justifyContent:'center', flexShrink:0 },
  title:      { fontSize:13, fontWeight:600, color:'#F1F5F9' },
  sub:        { fontSize:11, color:'#94A3B8' },
  badge:      { background:'#EF4444', color:'white', width:20, height:20, borderRadius:'50%', display:'flex', alignItems:'center', justifyContent:'center', fontSize:11, fontWeight:700, flexShrink:0 },
  list:       { display:'flex', flexDirection:'column', gap:6, maxHeight:320, overflowY:'auto' },
  loader:     { textAlign:'center', color:'#6B7280', fontSize:13, padding:'32px 0' },
  empty:      { display:'flex', flexDirection:'column', alignItems:'center', gap:8, padding:'32px 0' },
  emptyText:  { fontSize:13, color:'#94A3B8' },
  alert:      { borderRadius:8, padding:'10px 12px', display:'flex', gap:10 },
  alertBody:  { flex:1, minWidth:0 },
  alertTop:   { display:'flex', alignItems:'center', gap:5, flexWrap:'wrap', marginBottom:3 },
  company:    { fontSize:12, fontWeight:600, color:'#F1F5F9' },
  tag:        { fontSize:10, padding:'1px 6px', borderRadius:4, fontWeight:500 },
  foreignTag: { fontSize:10, padding:'1px 6px', borderRadius:4, background:'#F9730022', color:'#FDBA74', border:'1px solid #F9730040', display:'flex', alignItems:'center', gap:3 },
  alertDetail:{ fontSize:11, color:'#94A3B8' },
  alertLoc:   { fontSize:10, color:'#6B7280', marginTop:2 },
  dismissBtn: { fontSize:10, padding:'3px 8px', borderRadius:5, background:'#1E293B', color:'#94A3B8', border:'none', cursor:'pointer', flexShrink:0, alignSelf:'flex-start' },
};
