import ComingNext from './pages/ComingNext';
import ArticlePage from './pages/ArticlePage';
import ExplorePage from './pages/ExplorePage';
import ForgetPage from './pages/ForgetPage';
import HeadlinesPage from './pages/HeadlinesPage';
import HomePage from './pages/HomePage';
import InterestsPage from './pages/InterestsPage';
import PrivacyPage from './pages/PrivacyPage';
import ResearchPage from './pages/ResearchPage';
import StatusPage from './pages/StatusPage';
import VerificationPage from './pages/VerificationPage';

const RAW_ROUTES = [
  {
    path: '/', label: 'For you', icon: 'sparkles', group: 'news', component: HomePage,
    plan: {
      summary: 'Recommendations ranked by the dynamic long-term + short-term model.',
      uses: ['GET /api/v1/news/live', 'GET /api/v1/news', 'POST /recommend'],
    },
  },

  {
    path: '/headlines', label: 'Headlines', icon: 'newspaper', group: 'news', component: HeadlinesPage,
    plan: {
      summary: 'Live headlines. Not personalized and not popularity-ranked.',
      uses: ['GET /api/v1/news/live'],
      missing: 'No popularity/trending endpoint is exposed, so this page shows latest headlines, not "trending".',
    },
  },

  {
    path: '/explore', label: 'Explore', icon: 'compass', group: 'news', component: ExplorePage,
    plan: {
      summary: 'Browse by category or search the MIND catalog. Not personalized.',
      uses: ['GET /api/v1/news?category=&search=', 'GET /api/v1/news/live?category='],
    },
  },

  {
    path: '/article/:id', label: 'Article', nav: false, component: ArticlePage,
    plan: {
      summary: 'Opening an article sends a click event the model can use.',
      uses: ['GET /api/v1/news/{news_id}', 'POST /clicks'],
    },
  },

  {
    path: '/interests', label: 'My interests', icon: 'chart', group: 'data', component: InterestsPage,
    plan: {
      summary: 'Which parts of your profile the model is using right now.',
      uses: ['POST /recommend (used_long_term / used_short_term)', 'POST /clicks (acknowledged totals)'],
      missing: 'No endpoint exposes the profile vector or top terms, so this page can only show what the API reports.',
    },
  },

  {
    path: '/privacy', label: 'Privacy & consent', icon: 'lock', group: 'data', component: PrivacyPage,
    plan: {
      summary: 'Your consent state as recorded by the backend.',
      uses: ['GET /api/v1/users/{user_id}'],
      missing: 'There is no per-user personalization ON/OFF endpoint. Only "forget" exists.',
    },
  },

  {
    path: '/forget', label: 'Forget my data', icon: 'trash', group: 'data', component: ForgetPage,
    plan: {
      summary: 'Submit a right-to-be-forgotten request and see the backend result.',
      uses: ['POST /api/v1/delete-user'],
    },
  },

  {
    path: '/status', label: 'Unlearning status', icon: 'refresh', group: 'data', component: StatusPage,
    plan: {
      summary: 'Status of your latest unlearning request.',
      uses: ['GET /api/v1/certificate/{user_id}', 'GET /api/v1/unlearning-status/{request_id}'],
    },
  },

  {
    path: '/verification', label: 'Verification', icon: 'shield-check', group: 'data', component: VerificationPage,
    plan: {
      summary: 'Signed deletion certificate, Merkle proof and audit ledger.',
      uses: [
        'GET /api/v1/certificate/{user_id}',
        'POST /api/v1/verify-certificate',
        'GET /api/v1/auditor/audit-trail',
      ],
    },
  },

  {
    path: '/research', label: 'Research', icon: 'flask', group: 'project', component: ResearchPage,
    plan: {
      summary: 'Offline experiment results for the base recommendation model.',
      uses: ['Static results from results/*.csv', 'GET /health'],
    },
  },
];

export const ROUTES = RAW_ROUTES.map((r) => ({
  ...r,
  render: (params) =>
    r.component ? <r.component {...params} /> : <ComingNext route={r} />,
}));
