import { useState, useCallback } from 'react';
import { useApi } from './hooks/useApi';
import { api } from './services/api';
import NavBar       from './components/NavBar';
import StatCards    from './components/StatCards';
import Heatmap      from './components/Heatmap';
import EntityLinker from './components/EntityLinker';
import TrendFeed    from './components/TrendFeed';
import AlertPanel   from './components/AlertPanel';

const POLL = 5 * 60 * 1000; // 5 min

export default function App() {
  const [lastUpdated, setLastUpdated] = useState('just now');
  const [alerts, setAlerts]           = useState(null);

  const statsApi    = useApi(useCallback(() => api.getStats(),     []), POLL);
  const provApi     = useApi(useCallback(() => api.getProvinces(), []), POLL);
  const clusterApi  = useApi(useCallback(() => api.getClusters(),  []), POLL);
  const alertsApiRaw= useApi(useCallback(() => api.getAlerts(),    []), POLL);

  // Keep a local copy of alerts so dismissals are instant
  const alertData = alerts ?? alertsApiRaw.data;

  const handleDismiss = useCallback((id) => {
    setAlerts(prev => (prev ?? alertsApiRaw.data ?? []).map(a =>
      a.id === id ? { ...a, dismissed: true } : a
    ));
  }, [alertsApiRaw.data]);

  const refreshAll = useCallback(async () => {
    await Promise.all([
      statsApi.refetch(),
      provApi.refetch(),
      clusterApi.refetch(),
      alertsApiRaw.refetch(),
    ]);
    setLastUpdated('just now');
  }, [statsApi, provApi, clusterApi, alertsApiRaw]);

  return (
    <div style={styles.app}>
      <style>{`
        @keyframes spin { to { transform: rotate(360deg); } }
        * { box-sizing: border-box; }
      `}</style>

      <NavBar onRefreshAll={refreshAll} lastUpdated={lastUpdated} />

      <main style={styles.main}>
        {/* KPI Row */}
        <StatCards stats={statsApi.data} loading={statsApi.loading} />

        {/* Heatmap + Entity Linker */}
        <div style={styles.row2}>
          <Heatmap   provinces={provApi.data}     loading={provApi.loading} />
          <EntityLinker clusters={clusterApi.data} loading={clusterApi.loading} />
        </div>

        {/* Trend Feed + Alerts */}
        <div style={styles.row2}>
          <TrendFeed />
          <AlertPanel
            alerts={alertData}
            loading={alertsApiRaw.loading && !alerts}
            onDismiss={handleDismiss}
          />
        </div>
      </main>

      <footer style={styles.footer}>
        PNG Business Transparency Monitor · Data sourced from IPA, National Gazette, NPC, PNG Business News ·
        Not affiliated with the Investment Promotion Authority of Papua New Guinea
      </footer>
    </div>
  );
}

const styles = {
  app:    { minHeight:'100vh', background:'#0A0E1A', color:'#F1F5F9' },
  main:   { padding:'0 0 24px', display:'flex', flexDirection:'column', gap:12 },
  row2:   { display:'grid', gridTemplateColumns:'repeat(var(--row-cols, 2), 1fr)', gap:12, padding:'0 var(--side-padding, 24px)' },
  footer: { padding:'16px var(--side-padding, 24px)', textAlign:'center', fontSize:10, color:'#4B5563', borderTop:'1px solid #1E293B' },
};
