import { useEffect, useState } from 'react';
import { useLocation } from '../router/router';
import MobileNav from './MobileNav';
import Sidebar from './Sidebar';
import TopBar from './TopBar';

export default function Shell({ children }) {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const { path } = useLocation();

  useEffect(() => {
    setDrawerOpen(false);
  }, [path]);

  return (
    <div className="cf-shell">
      <a className="cf-skip" href="#main">Skip to content</a>

      <aside className={`cf-sidebar ${drawerOpen ? 'is-open' : ''}`}>
        <Sidebar onNavigate={() => setDrawerOpen(false)} />
      </aside>
      {drawerOpen && (
        <button type="button" className="cf-scrim" aria-label="Close menu" onClick={() => setDrawerOpen(false)} />
      )}

      <div className="cf-main">
        <TopBar onMenu={() => setDrawerOpen(true)} />
        <main className="cf-content" id="main">
          {children}
        </main>
      </div>

      <MobileNav onMenu={() => setDrawerOpen(true)} />
    </div>
  );
}