import { Fragment, useEffect, useMemo, useSyncExternalStore } from 'react';

function subscribe(callback) {
  window.addEventListener('hashchange', callback);
  return () => window.removeEventListener('hashchange', callback);
}
const getHash = () => window.location.hash.slice(1) || '/';

export function useLocation() {
  const raw = useSyncExternalStore(subscribe, getHash, () => '/');
  return useMemo(() => {
    const i = raw.indexOf('?');
    const path = (i === -1 ? raw : raw.slice(0, i)) || '/';
    const query = Object.fromEntries(new URLSearchParams(i === -1 ? '' : raw.slice(i + 1)));
    return { raw, path, query };
  }, [raw]);
}

export function navigate(to, { replace = false } = {}) {
  if (replace) window.location.replace(`#${to}`);
  else window.location.hash = to;
}

export function matchPath(pattern, path) {
  const a = pattern.split('/').filter(Boolean);
  const b = path.split('/').filter(Boolean);
  if (a.length !== b.length) return null;
  const params = {};
  for (let i = 0; i < a.length; i += 1) {
    if (a[i].startsWith(':')) params[a[i].slice(1)] = decodeURIComponent(b[i]);
    else if (a[i] !== b[i]) return null;
  }
  return params;
}

export function isActive(currentPath, to) {
  if (to === '/') return currentPath === '/';
  return currentPath === to || currentPath.startsWith(`${to}/`);
}

export function Link({ to, children, ...rest }) {
  return (
    <a href={`#${to}`} {...rest}>
      {children}
    </a>
  );
}

export function Routes({ routes, notFound }) {
  const loc = useLocation();

  useEffect(() => {
    window.scrollTo(0, 0);
  }, [loc.path]);

  for (const route of routes) {
    const params = matchPath(route.path, loc.path);
    if (params) {
      return <Fragment key={loc.path}>{route.render(params, loc)}</Fragment>;
    }
  }
  return notFound ? notFound(loc) : null;
}