import { useState, useEffect, useCallback } from 'react';

/**
 * Generic API hook.
 * @param {Function} fetcher  - async function that returns data
 * @param {number}   interval - auto-refresh ms (0 = no polling)
 */
export function useApi(fetcher, interval = 0) {
  const [data, setData]       = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState(null);

  const load = useCallback(async () => {
    try {
      setLoading(true);
      const result = await fetcher();
      setData(result);
      setError(null);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [fetcher]);

  useEffect(() => {
    load();
    if (!interval) return;
    const id = setInterval(load, interval);
    return () => clearInterval(id);
  }, [load, interval]);

  return { data, loading, error, refetch: load };
}
