import { useEffect, useState } from 'react';
import { api } from '../cryptoforge/api/client';
import { useApp } from '../cryptoforge/state/AppState';

const IDLE = { status: 'idle', usedLong: false, usedShort: false, modelVersion: null, error: null };

// Asks POST /recommend which parts of the profile exist for the current user.
// status: 'idle' | 'loading' | 'ready' | 'error'
export function useProfileProbe() {
  const { userId, health, personalization, backendClickTotal } = useApp();
  const [state, setState] = useState(IDLE);
  const [nonce, setNonce] = useState(0);

  useEffect(() => {
    if (personalization !== 'on' || health.online !== true) {
      setState(IDLE);
      return undefined;
    }

    let cancelled = false;
    setState((s) => ({ ...s, status: 'loading', error: null }));

    (async () => {
      try {
        const pool = await api.mindNews({ limit: 10 });
        const ids = (pool.articles || []).map((a) => a.news_id);
        if (ids.length === 0) throw new Error('No MIND articles were available to probe with.');
        const res = await api.recommend({ userId, candidateIds: ids, topK: ids.length });
        if (!cancelled) {
          setState({
            status: 'ready',
            usedLong: res.used_long_term,
            usedShort: res.used_short_term,
            modelVersion: res.model_version,
            error: null,
          });
        }
      } catch (err) {
        if (!cancelled) setState({ ...IDLE, status: 'error', error: err.message });
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [userId, personalization, health.online, backendClickTotal, nonce]);

  return { ...state, refresh: () => setNonce((n) => n + 1) };
}
