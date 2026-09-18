import React, { useState, useEffect } from 'react';
import { 
  Sparkles, BookOpen, Clock, Tag, RefreshCw, 
  CheckCircle2, ArrowRight, X, AlertCircle, Eye
} from 'lucide-react';

const API_BASE = 'http://localhost:8000';

const CATEGORIES = ['All', 'news', 'sports', 'finance', 'entertainment', 'lifestyle', 'travel'];

export default function NewsFeed({ currentUser, onArticleClicked }) {
  const [articles, setArticles] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [loadingNews, setLoadingNews] = useState(false);
  const [loadingRecs, setLoadingRecs] = useState(false);
  const [activeArticle, setActiveArticle] = useState(null);
  const [clickMessage, setClickMessage] = useState('');

  // Fetch News Catalog
  useEffect(() => {
    fetchNewsCatalog(selectedCategory);
  }, [selectedCategory]);

  // Fetch Recommendations for active user
  useEffect(() => {
    if (currentUser && !currentUser.is_unlearned) {
      fetchRecommendations();
    } else {
      setRecommendations([]);
    }
  }, [currentUser, selectedCategory]);

  const fetchNewsCatalog = async (cat) => {
    setLoadingNews(true);
    try {
      const url = `${API_BASE}/api/v1/news?limit=12&category=${cat === 'All' ? '' : cat}`;
      const res = await fetch(url);
      if (res.ok) {
        const data = await res.json();
        setArticles(data.articles || []);
      }
    } catch (err) {
      console.error('Failed to fetch news catalog:', err);
    } finally {
      setLoadingNews(false);
    }
  };

  const fetchRecommendations = async () => {
    setLoadingRecs(true);
    try {
      const candidateIds = articles.map(a => a.news_id);
      if (candidateIds.length === 0) return;

      const res = await fetch(`${API_BASE}/recommend`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: currentUser.user_id,
          candidate_news_ids: candidateIds.slice(0, 10),
          top_k: 3
        })
      });

      if (res.ok) {
        const data = await res.json();
        const recList = data.recommendations || [];
        // Map recommendation IDs back to full article metadata
        const fullRecs = recList.map(r => {
          const match = articles.find(a => a.news_id === r.news_id);
          return match ? { ...match, score: r.score } : null;
        }).filter(Boolean);
        setRecommendations(fullRecs);
      }
    } catch (err) {
      console.error('Failed to fetch recommendations:', err);
    } finally {
      setLoadingRecs(false);
    }
  };

  // Open Article & Record Click
  const handleOpenArticle = async (article) => {
    setActiveArticle(article);
    setClickMessage('');

    if (currentUser) {
      try {
        const res = await fetch(`${API_BASE}/clicks`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            user_id: currentUser.user_id,
            news_id: article.news_id
          })
        });
        if (res.ok) {
          setClickMessage(`Interaction recorded! Added ${article.news_id} to short-term profile.`);
          if (onArticleClicked) onArticleClicked();
        }
      } catch (err) {
        console.error('Failed to record click:', err);
      }
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
      
      {/* Category Filter Pills */}
      <div style={{ display: 'flex', gap: '10px', overflowX: 'auto', paddingBottom: '4px' }}>
        {CATEGORIES.map((cat) => (
          <button
            key={cat}
            onClick={() => setSelectedCategory(cat)}
            style={{
              padding: '8px 18px',
              borderRadius: '20px',
              border: `1px solid ${selectedCategory === cat ? '#38bdf8' : 'var(--border-color)'}`,
              background: selectedCategory === cat ? 'rgba(56, 189, 248, 0.15)' : '#111827',
              color: selectedCategory === cat ? '#38bdf8' : 'var(--text-secondary)',
              fontSize: '13px',
              fontWeight: '600',
              cursor: 'pointer',
              textTransform: 'capitalize',
              whiteSpace: 'nowrap'
            }}
          >
            {cat}
          </button>
        ))}
      </div>

      {/* AI Personalization Recommendation Hero Section */}
      <div className="glass-card" style={{ padding: '24px', position: 'relative', overflow: 'hidden' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Sparkles size={22} color="#818cf8" />
            <h2 style={{ fontSize: '18px', fontWeight: '700' }} className="gradient-text">
              Personalized News Feed for {currentUser?.name || 'You'}
            </h2>
          </div>

          {currentUser?.is_unlearned ? (
            <span style={{ fontSize: '12px', padding: '4px 12px', borderRadius: '12px', background: 'rgba(244, 63, 94, 0.15)', color: '#f43f5e', border: '1px solid rgba(244, 63, 94, 0.3)', fontWeight: '600' }}>
              🔒 Non-Personalized Mode (Model Access Revoked)
            </span>
          ) : (
            <button
              onClick={fetchRecommendations}
              disabled={loadingRecs}
              style={{ padding: '6px 14px', borderRadius: '8px', background: '#1f2937', color: '#fff', border: '1px solid var(--border-color)', fontSize: '12px', fontWeight: '600', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px' }}
            >
              {loadingRecs ? <RefreshCw className="animate-spin" size={14} /> : <RefreshCw size={14} />} Refresh AI Ranking
            </button>
          )}
        </div>

        {currentUser?.is_unlearned ? (
          <div style={{ padding: '20px', borderRadius: '12px', background: 'rgba(255, 255, 255, 0.02)', textAlign: 'center', color: 'var(--text-muted)', fontSize: '13px' }}>
            You have revoked data consent and unlearned your profile from the model. Articles are served in random/popular order without tracking your behavior.
          </div>
        ) : recommendations.length > 0 ? (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px' }}>
            {recommendations.map((rec) => (
              <div
                key={rec.news_id}
                onClick={() => handleOpenArticle(rec)}
                style={{
                  padding: '16px',
                  borderRadius: '12px',
                  background: '#1f2937',
                  border: '1px solid rgba(99, 102, 241, 0.3)',
                  cursor: 'pointer',
                  display: 'flex',
                  flexDirection: 'column',
                  justify: 'space-between',
                  gap: '12px',
                  transition: 'transform 0.2s'
                }}
              >
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                    <span style={{ fontSize: '11px', padding: '2px 8px', borderRadius: '10px', background: 'rgba(99, 102, 241, 0.2)', color: '#818cf8', fontWeight: '700', textTransform: 'uppercase' }}>
                      {rec.category}
                    </span>
                    <span style={{ fontSize: '11px', color: '#10b981', fontWeight: '600' }}>
                      {(rec.score * 100).toFixed(0)}% Match
                    </span>
                  </div>
                  <h4 style={{ fontSize: '14px', fontWeight: '700', color: '#f9fafb', lineHeight: '1.4' }}>{rec.title}</h4>
                </div>

                <div style={{ fontSize: '12px', color: '#38bdf8', display: 'flex', alignItems: 'center', gap: '4px', fontWeight: '600' }}>
                  Read Article <ArrowRight size={14} />
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div style={{ padding: '20px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '13px' }}>
            Click articles below to build your interaction profile and unlock personalized recommendations.
          </div>
        )}
      </div>

      {/* Explore Main News Grid */}
      <div>
        <h3 style={{ fontSize: '18px', fontWeight: '700', marginBottom: '16px', color: '#f3f4f6' }}>
          Explore Latest News ({articles.length} Articles)
        </h3>

        {loadingNews ? (
          <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
            <RefreshCw className="animate-spin" size={24} style={{ margin: '0 auto 12px' }} />
            Loading MIND news catalog...
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '20px' }}>
            {articles.map((art) => (
              <div
                key={art.news_id}
                onClick={() => handleOpenArticle(art)}
                className="glass-card"
                style={{
                  padding: '20px',
                  display: 'flex',
                  flexDirection: 'column',
                  justify: 'space-between',
                  gap: '14px',
                  cursor: 'pointer'
                }}
              >
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                    <span style={{ fontSize: '11px', padding: '3px 10px', borderRadius: '12px', background: 'rgba(56, 189, 248, 0.15)', color: '#38bdf8', fontWeight: '700', textTransform: 'uppercase' }}>
                      {art.category}
                    </span>
                    <span style={{ fontSize: '11px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                      ID: {art.news_id}
                    </span>
                  </div>

                  <h4 style={{ fontSize: '15px', fontWeight: '700', color: '#f9fafb', lineHeight: '1.4', marginBottom: '8px' }}>
                    {art.title}
                  </h4>

                  <p style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: '1.5', display: '-webkit-box', WebkitLineClamp: 3, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>
                    {art.abstract || 'Read full article details, category tags, and personalized recommendation metrics.'}
                  </p>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: '12px', borderTop: '1px solid var(--border-color)', fontSize: '12px' }}>
                  <span style={{ color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <Clock size={14} /> 2 min read
                  </span>
                  <span style={{ color: '#818cf8', fontWeight: '600', display: 'flex', alignItems: 'center', gap: '4px' }}>
                    <Eye size={14} /> Read & Record Click
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Article Detail Reader Modal */}
      {activeArticle && (
        <div style={{
          position: 'fixed',
          top: 0, left: 0, right: 0, bottom: 0,
          background: 'rgba(0, 0, 0, 0.8)',
          backdropFilter: 'blur(8px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000,
          padding: '20px'
        }}>
          <div className="glass-card" style={{ maxWidth: '650px', width: '100%', padding: '28px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
            
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <span style={{ fontSize: '12px', padding: '4px 12px', borderRadius: '12px', background: 'rgba(56, 189, 248, 0.2)', color: '#38bdf8', fontWeight: '700', textTransform: 'uppercase' }}>
                {activeArticle.category} / {activeArticle.subcategory || 'General'}
              </span>
              <button onClick={() => setActiveArticle(null)} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}>
                <X size={20} />
              </button>
            </div>

            <h2 style={{ fontSize: '20px', fontWeight: '800', color: '#f9fafb', lineHeight: '1.4' }}>
              {activeArticle.title}
            </h2>

            <p style={{ fontSize: '14px', color: '#d1d5db', lineHeight: '1.6' }}>
              {activeArticle.abstract || 'Full article content loaded from the Microsoft News Dataset (MIND). Reading this article registers an interaction in your short-term dynamic recommendation profile.'}
            </p>

            {clickMessage && (
              <div style={{ padding: '12px', borderRadius: '8px', background: 'rgba(16, 185, 129, 0.15)', border: '1px solid rgba(16, 185, 129, 0.3)', color: '#10b981', fontSize: '13px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <CheckCircle2 size={16} /> {clickMessage}
              </div>
            )}

            <div style={{ display: 'flex', justifyContent: 'flex-end', paddingTop: '16px', borderTop: '1px solid var(--border-color)' }}>
              <button
                onClick={() => setActiveArticle(null)}
                style={{ padding: '10px 20px', borderRadius: '8px', background: 'linear-gradient(135deg, #6366f1 0%, #3b82f6 100%)', color: '#fff', border: 'none', fontWeight: '600', cursor: 'pointer' }}
              >
                Done Reading
              </button>
            </div>

          </div>
        </div>
      )}

    </div>
  );
}
