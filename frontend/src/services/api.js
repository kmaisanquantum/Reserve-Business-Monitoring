const BASE = process.env.REACT_APP_API_URL
  ? `https://${process.env.REACT_APP_API_URL}`
  : 'http://localhost:8000';

async function req(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) throw new Error(`API ${path} → ${res.status}`);
  return res.json();
}

export const api = {
  getStats:       ()         => req('/api/stats'),
  getProvinces:   ()         => req('/api/provinces'),
  getClusters:    ()         => req('/api/clusters'),
  getTrends:      (cat='all')=> req(`/api/trends?category=${encodeURIComponent(cat)}&limit=20`),
  getAlerts:      ()         => req('/api/alerts'),
  dismissAlert:   (id)       => req(`/api/alerts/${id}/dismiss`, { method: 'POST' }),
  triggerScrape:  ()         => req('/api/scrape/trigger', { method: 'POST' }),
  getScrapeStatus:()         => req('/api/scrape/status'),
  search:         (q)        => req(`/api/search?q=${encodeURIComponent(q)}`),
};
