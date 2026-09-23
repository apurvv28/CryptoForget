// In dev (vite on :5173) talk to the FastAPI server on :8000.
// When the build is served by FastAPI itself, use same-origin.
// Override with VITE_API_BASE in frontend/.env if needed.
const BASE =
  import.meta.env.VITE_API_BASE ??
  (import.meta.env.DEV ? 'http://localhost:8000' : '');

export class ApiError extends Error {
  constructor(message, status = 0, detail = null) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.detail = detail;
  }
}

async function request(path, { method = 'GET', body, params, signal } = {}) {
  const url = new URL(`${BASE}${path}`, window.location.origin);
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        url.searchParams.set(key, String(value));
      }
    });
  }

  let res;
  try {
    res = await fetch(url, {
      method,
      signal,
      headers: body ? { 'Content-Type': 'application/json' } : undefined,
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch (err) {
    if (err.name === 'AbortError') throw err;
    throw new ApiError('Cannot reach the CryptoForget API. Is the backend running?');
  }

  if (!res.ok) {
    let detail = null;
    try {
      detail = (await res.json()).detail ?? null;
    } catch {
      /* non-JSON error body */
    }
    const message =
      typeof detail === 'string' ? detail : `Request failed (${res.status})`;
    throw new ApiError(message, res.status, detail);
  }
  return res.json();
}

export const api = {
  // System
  health: (opts) => request('/health', opts),

  // Demo users (simulated agents)
  listUsers: (opts) => request('/api/v1/users', opts),
  getUser: (userId, opts) => request(`/api/v1/users/${encodeURIComponent(userId)}`, opts),
  resetAllDeletions: () => request('/api/v1/users/reset-all-deletions', { method: 'POST' }),

  // News catalog
  liveNews: ({ category, limit = 40 } = {}, opts) =>
    request('/api/v1/news/live', { params: { category, limit }, ...opts }),
  mindNews: ({ category, search, limit = 60, offset = 0 } = {}, opts) =>
    request('/api/v1/news', {
      params: { category, search, limit, offset, include_live: false },
      ...opts,
    }),
  // Progressive image lookup for live articles: { images, pending, missing }
  newsImages: (ids, opts) =>
    request('/api/v1/news/images', { params: { ids: ids.join(',') }, ...opts }),
  getNews: (newsId, opts) => request(`/api/v1/news/${encodeURIComponent(newsId)}`, opts),

  // Recommendation model + interactions
  recommend: ({ userId, candidateIds, topK }, opts) =>
    request('/recommend', {
      method: 'POST',
      body: {
        user_id: userId,
        candidate_news_ids: candidateIds,
        top_k: Math.min(Math.max(topK ?? candidateIds.length, 1), 100),
      },
      ...opts,
    }),
  recordClick: ({ userId, newsId }) =>
    request('/clicks', { method: 'POST', body: { user_id: userId, news_id: newsId } }),

  // Unlearning + verification (used in later batches)
  deleteUser: ({ userId, deletionType }) =>
    request('/api/v1/delete-user', {
      method: 'POST',
      body: { user_id: userId, deletion_type: deletionType },
    }),
  unlearningStatus: (requestId, opts) =>
    request(`/api/v1/unlearning-status/${encodeURIComponent(requestId)}`, opts),
  certificate: (userId, opts) =>
    request(`/api/v1/certificate/${encodeURIComponent(userId)}`, opts),
  verifyCertificate: (certificate) =>
    request('/api/v1/verify-certificate', { method: 'POST', body: { certificate } }),
  auditTrail: (opts) => request('/api/v1/auditor/audit-trail', opts),
};