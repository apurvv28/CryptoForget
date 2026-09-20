import Shell from './layout/Shell';
import { Routes } from './router/router';
import { ROUTES } from './routes';
import { AppProvider } from './state/AppState';
import './styles/articles.css';
import './styles/privacy.css';
   import './styles/insights.css';

function NotFound() {
  return (
    <div className="cf-page-head">
      <h1>Page not found</h1>
      <p>That address doesn't match any screen. Use the sidebar to navigate.</p>
    </div>
  );
}
export default function CryptoForgeApp() {
  return (
    <AppProvider>
      <Shell>
        <Routes routes={ROUTES} notFound={() => <NotFound />} />
      </Shell>
    </AppProvider>
  );
}