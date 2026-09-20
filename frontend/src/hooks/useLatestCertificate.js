import { useEffect, useState } from 'react';
import { api } from '../cryptoforge/api/client';
import { useApp } from '../cryptoforge/state/AppState';

// status: 'loading' | 'ready' | 'none' | 'error'
export function useLatestCertificate() {
  const { health, userId } = useApp();
  const [state, setState] = useState({ status: 'loading', certificate: null, error: null });
  const [nonce, setNonce] = useState(0);

  useEffect(() => {
    if (health.online === null) return undefined;
    if (health.online === false) {
      setState({ status: 'error', certificate: null, error: 'Cannot reach the CryptoForget API.' });
      return undefined;
    }

    let cancelled = false;
    setState({ status: 'loading', certificate: null, error: null });

    api
      .certificate(userId)
      .then((certificate) => {
        if (!cancelled) setState({ status: 'ready', certificate, error: null });
      })
      .catch((err) => {
        if (cancelled) return;
        if (err.status === 404) setState({ status: 'none', certificate: null, error: null });
        else setState({ status: 'error', certificate: null, error: err.message });
      });

    return () => {
      cancelled = true;
    };
  }, [userId, health.online, nonce]);

  return { ...state, reload: () => setNonce((n) => n + 1) };
}