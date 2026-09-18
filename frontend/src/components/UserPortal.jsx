import React, { useState, useEffect } from 'react';
import { 
  User, Shield, Trash2, CheckCircle2, Clock, 
  Sparkles, ExternalLink, Zap, AlertCircle, RefreshCw, FileCheck
} from 'lucide-react';

const API_BASE = 'http://localhost:8000';

export default function UserPortal({ onSelectCertificate }) {
  const [agents, setAgents] = useState([]);
  const [selectedUserId, setSelectedUserId] = useState('U1000');
  const [currentAgent, setCurrentAgent] = useState(null);
  const [candidates, setCandidates] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [loadingRecs, setLoadingRecs] = useState(false);
  const [deletionType, setDeletionType] = useState('Path B');
  const [unlearningStatus, setUnlearningStatus] = useState('idle'); // idle, processing, completed
  const [unlearningResult, setUnlearningResult] = useState(null);
  const [errorMessage, setErrorMessage] = useState('');

  // Fetch list of virtual user agents
  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/users`);
      if (res.ok) {
        const data = await res.json();
        setAgents(data);
        if (data.length > 0 && !selectedUserId) {
          setSelectedUserId(data[0].user_id);
        }
      }
    } catch (err) {
      console.error('Failed to fetch users:', err);
    }
  };

  // Fetch selected user agent profile
  useEffect(() => {
    if (selectedUserId) {
      fetchAgentDetails(selectedUserId);
    }
  }, [selectedUserId]);

  const fetchAgentDetails = async (uid) => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/users/${uid}`);
      if (res.ok) {
        const data = await res.json();
        setCurrentAgent(data);
      }
    } catch (err) {
      console.error('Failed to fetch agent details:', err);
    }
  };

  // Trigger News Recommendation
  const fetchRecommendations = async () => {
    setLoadingRecs(true);
    setErrorMessage('');
    const sampleCandidates = [
      'N10001', 'N10002', 'N10003', 'N10004', 'N10005',
      'N10006', 'N10007', 'N10008', 'N10009', 'N10010'
    ];
    setCandidates(sampleCandidates);

    try {
      const res = await fetch(`${API_BASE}/recommend`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: selectedUserId,
          candidate_news_ids: sampleCandidates,
          top_k: 5
        })
      });

      if (res.ok) {
        const data = await res.json();
        setRecommendations(data.recommendations || []);
      } else {
        const errData = await res.json();
        setErrorMessage(errData.detail || 'Failed to generate recommendations.');
      }
    } catch (err) {
      setErrorMessage('Backend API unreachable. Ensure uvicorn main:app is running.');
    } finally {
      setLoadingRecs(false);
    }
  };

  // Record Click
  const handleRecordClick = async (newsId) => {
    try {
      const res = await fetch(`${API_BASE}/clicks`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: selectedUserId,
          news_id: newsId
        })
      });
      if (res.ok) {
        fetchAgentDetails(selectedUserId);
      }
    } catch (err) {
      console.error('Failed to record click:', err);
    }
  };

  // Trigger Unlearning / Data Deletion
  const handleUnlearnRequest = async () => {
    setUnlearningStatus('processing');
    setErrorMessage('');

    try {
      const res = await fetch(`${API_BASE}/api/v1/delete-user`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: selectedUserId,
          deletion_type: deletionType
        })
      });

      if (res.ok) {
        const data = await res.json();
        setUnlearningResult(data);
        setUnlearningStatus('completed');
        fetchAgentDetails(selectedUserId);
        fetchUsers();
      } else {
        const errData = await res.json();
        setErrorMessage(errData.detail || 'Unlearning execution failed.');
        setUnlearningStatus('idle');
      }
    } catch (err) {
      setErrorMessage('Error communicating with unlearning engine.');
      setUnlearningStatus('idle');
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      
      {/* Top Banner: Agent Selector & Status */}
      <div className="glass-card" style={{ padding: '24px', display: 'flex', flexWrap: 'wrap', gap: '24px', alignItems: 'center', justifyContent: 'space-between' }}>
        
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{ padding: '12px', borderRadius: '12px', background: 'rgba(99, 102, 241, 0.15)', color: '#818cf8' }}>
            <User size={28} />
          </div>
          <div>
            <label style={{ fontSize: '12px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Select Virtual User Agent (15-20 Population)
            </label>
            <select
              value={selectedUserId}
              onChange={(e) => setSelectedUserId(e.target.value)}
              style={{
                display: 'block',
                marginTop: '4px',
                padding: '8px 16px',
                borderRadius: '8px',
                background: '#1f2937',
                color: '#fff',
                border: '1px solid var(--border-color)',
                fontSize: '16px',
                fontWeight: '600',
                outline: 'none',
                cursor: 'pointer'
              }}
            >
              {agents.map((agent) => (
                <option key={agent.user_id} value={agent.user_id}>
                  {agent.user_id} - {agent.name} ({agent.category_preference}) {agent.is_unlearned ? '🔒 [UNLEARNED]' : ''}
                </option>
              ))}
            </select>
          </div>
        </div>

        {currentAgent && (
          <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: '14px', fontWeight: '600', color: '#f3f4f6' }}>{currentAgent.name}</div>
              <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{currentAgent.email}</div>
            </div>
            
            <div style={{
              padding: '6px 14px',
              borderRadius: '20px',
              fontSize: '12px',
              fontWeight: '600',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              background: currentAgent.is_unlearned ? 'rgba(244, 63, 94, 0.15)' : 'rgba(16, 185, 129, 0.15)',
              color: currentAgent.is_unlearned ? '#f43f5e' : '#10b981',
              border: `1px solid ${currentAgent.is_unlearned ? 'rgba(244, 63, 94, 0.3)' : 'rgba(16, 185, 129, 0.3)'}`
            }}>
              <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: currentAgent.is_unlearned ? '#f43f5e' : '#10b981' }}></span>
              {currentAgent.is_unlearned ? 'UNLEARNED (OPTED OUT)' : 'ACTIVE (CONSENT GIVEN)'}
            </div>

            <div style={{
              padding: '6px 14px',
              borderRadius: '20px',
              fontSize: '12px',
              fontWeight: '600',
              background: 'rgba(6, 182, 212, 0.15)',
              color: '#06b6d4',
              border: '1px solid rgba(6, 182, 212, 0.3)'
            }}>
              SISA Shard #{currentAgent.shard_id}
            </div>
          </div>
        )}
      </div>

      {errorMessage && (
        <div style={{ padding: '16px', borderRadius: '12px', background: 'rgba(244, 63, 94, 0.15)', border: '1px solid rgba(244, 63, 94, 0.3)', color: '#f43f5e', display: 'flex', alignItems: 'center', gap: '12px' }}>
          <AlertCircle size={20} />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Main Grid: Recommendation Engine & Right-to-be-Forgotten Panel */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '24px' }}>
        
        {/* Left Column: Live Recommendation Engine */}
        <div className="glass-card" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <h3 style={{ fontSize: '18px', fontWeight: '700' }} className="gradient-text">
                Live News Recommendation
              </h3>
              <p style={{ fontSize: '13px', color: 'var(--text-muted)', marginTop: '2px' }}>
                Serves dynamic model predictions using long-term history + live click profile
              </p>
            </div>

            <button
              onClick={fetchRecommendations}
              disabled={loadingRecs || currentAgent?.is_unlearned}
              style={{
                padding: '10px 18px',
                borderRadius: '10px',
                background: currentAgent?.is_unlearned ? '#374151' : 'linear-gradient(135deg, #6366f1 0%, #3b82f6 100%)',
                color: '#fff',
                border: 'none',
                fontWeight: '600',
                cursor: currentAgent?.is_unlearned ? 'not-allowed' : 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}
            >
              {loadingRecs ? <RefreshCw className="animate-spin" size={16} /> : <Zap size={16} />}
              Get Recommendations
            </button>
          </div>

          {currentAgent?.is_unlearned ? (
            <div style={{ padding: '32px', textAlign: 'center', background: 'rgba(255, 255, 255, 0.02)', borderRadius: '12px', border: '1px dashed var(--border-color)' }}>
              <Shield size={40} color="#f43f5e" style={{ margin: '0 auto 12px' }} />
              <h4 style={{ color: '#f43f5e', fontSize: '16px' }}>Personalization Revoked</h4>
              <p style={{ fontSize: '13px', color: 'var(--text-muted)', marginTop: '4px' }}>
                This user agent has executed data unlearning. Recommendation requests return non-personalized baseline output.
              </p>
            </div>
          ) : recommendations.length === 0 ? (
            <div style={{ padding: '32px', textAlign: 'center', background: 'rgba(255, 255, 255, 0.02)', borderRadius: '12px', border: '1px dashed var(--border-color)' }}>
              <Sparkles size={32} color="#818cf8" style={{ margin: '0 auto 12px' }} />
              <p style={{ fontSize: '14px', color: 'var(--text-muted)' }}>
                Click "Get Recommendations" to rank candidate news articles for {currentAgent?.user_id}.
              </p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {recommendations.map((rec, idx) => (
                <div key={rec.news_id} style={{
                  padding: '14px 16px',
                  borderRadius: '12px',
                  background: '#1f2937',
                  border: '1px solid var(--border-color)',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center'
                }}>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <span style={{ fontSize: '12px', fontWeight: '700', color: '#818cf8' }}>#{idx + 1}</span>
                      <span style={{ fontSize: '15px', fontWeight: '600', color: '#f9fafb' }}>Article {rec.news_id}</span>
                    </div>
                    <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '4px' }}>
                      Cosine Similarity Score: {(rec.score * 100).toFixed(2)}%
                    </div>
                  </div>

                  <button
                    onClick={() => handleRecordClick(rec.news_id)}
                    style={{
                      padding: '6px 12px',
                      borderRadius: '6px',
                      background: 'rgba(16, 185, 129, 0.15)',
                      color: '#10b981',
                      border: '1px solid rgba(16, 185, 129, 0.3)',
                      fontSize: '12px',
                      fontWeight: '600',
                      cursor: 'pointer'
                    }}
                  >
                    + Record Click
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Right Column: Right-to-be-Forgotten Action Center */}
        <div className="glass-card" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div>
            <h3 style={{ fontSize: '18px', fontWeight: '700' }} className="gradient-text-emerald">
              Right-to-be-Forgotten Action Center
            </h3>
            <p style={{ fontSize: '13px', color: 'var(--text-muted)', marginTop: '2px' }}>
              GDPR Article 17 / CCPA Verifiable Data Unlearning Engine
            </p>
          </div>

          {/* Deletion Type Selector */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <label style={{ fontSize: '12px', fontWeight: '600', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
              Select Unlearning Path
            </label>
            
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
              <button
                onClick={() => setDeletionType('Path A')}
                style={{
                  padding: '14px',
                  borderRadius: '10px',
                  border: `1px solid ${deletionType === 'Path A' ? '#10b981' : 'var(--border-color)'}`,
                  background: deletionType === 'Path A' ? 'rgba(16, 185, 129, 0.15)' : '#1f2937',
                  color: '#fff',
                  textAlign: 'left',
                  cursor: 'pointer'
                }}
              >
                <div style={{ fontSize: '14px', fontWeight: '700', color: deletionType === 'Path A' ? '#10b981' : '#fff' }}>Path A (Pre-training)</div>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px' }}>Feature Store Tombstoning (Before retraining)</div>
              </button>

              <button
                onClick={() => setDeletionType('Path B')}
                style={{
                  padding: '14px',
                  borderRadius: '10px',
                  border: `1px solid ${deletionType === 'Path B' ? '#6366f1' : 'var(--border-color)'}`,
                  background: deletionType === 'Path B' ? 'rgba(99, 102, 241, 0.15)' : '#1f2937',
                  color: '#fff',
                  textAlign: 'left',
                  cursor: 'pointer'
                }}
              >
                <div style={{ fontSize: '14px', fontWeight: '700', color: deletionType === 'Path B' ? '#818cf8' : '#fff' }}>Path B (Post-training)</div>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px' }}>Selective SISA Shard Retraining</div>
              </button>
            </div>
          </div>

          {/* Action Button */}
          <button
            onClick={handleUnlearnRequest}
            disabled={unlearningStatus === 'processing' || currentAgent?.is_unlearned}
            style={{
              padding: '16px',
              borderRadius: '12px',
              background: currentAgent?.is_unlearned ? '#374151' : 'linear-gradient(135deg, #f43f5e 0%, #e11d48 100%)',
              color: '#fff',
              border: 'none',
              fontSize: '16px',
              fontWeight: '700',
              cursor: currentAgent?.is_unlearned ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '10px',
              boxShadow: currentAgent?.is_unlearned ? 'none' : '0 10px 25px -5px rgba(244, 63, 94, 0.5)'
            }}
          >
            {unlearningStatus === 'processing' ? (
              <>
                <RefreshCw className="animate-spin" size={20} />
                Retraining SISA Shard #{currentAgent?.shard_id}...
              </>
            ) : (
              <>
                <Trash2 size={20} />
                {currentAgent?.is_unlearned ? 'Data Already Unlearned' : `Stop / Delete My Data (${deletionType})`}
              </>
            )}
          </button>

          {/* Unlearning Success Result Card */}
          {unlearningStatus === 'completed' && unlearningResult && (
            <div style={{ padding: '16px', borderRadius: '12px', background: 'rgba(16, 185, 129, 0.12)', border: '1px solid rgba(16, 185, 129, 0.3)', display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: '#10b981', fontWeight: '700' }}>
                <CheckCircle2 size={20} />
                Unlearning Complete & Certificate Issued!
              </div>

              <div style={{ fontSize: '13px', color: '#d1d5db', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                <div><strong>Certificate ID:</strong> <span className="font-mono" style={{ color: '#06b6d4' }}>{unlearningResult.certificate.certificate_id}</span></div>
                <div><strong>Old Merkle Root:</strong> <span className="font-mono">{unlearningResult.certificate.old_merkle_root.slice(0, 16)}...</span></div>
                <div><strong>New Merkle Root:</strong> <span className="font-mono">{unlearningResult.certificate.new_merkle_root.slice(0, 16)}...</span></div>
                <div><strong>ECDSA Signature:</strong> <span className="font-mono" style={{ color: '#a78bfa' }}>{unlearningResult.certificate.ecdsa_signature.slice(0, 24)}...</span></div>
              </div>

              <button
                onClick={() => onSelectCertificate(unlearningResult.certificate)}
                style={{
                  padding: '10px',
                  borderRadius: '8px',
                  background: '#10b981',
                  color: '#090d16',
                  border: 'none',
                  fontWeight: '700',
                  fontSize: '13px',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '6px'
                }}
              >
                <FileCheck size={16} />
                Inspect & Verify Deletion Certificate
              </button>
            </div>
          )}

        </div>

      </div>

    </div>
  );
}
