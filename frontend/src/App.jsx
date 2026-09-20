import React, { useState, useEffect } from 'react';
import { 
  ShieldCheck, User, Settings, Lock, Activity, 
  Newspaper, Sparkles, CheckCircle2, AlertCircle, RefreshCw 
} from 'lucide-react';
import NewsFeed from './components/NewsFeed';
import UserProfileSettings from './components/UserProfileSettings';
import AuditorPortal from './components/AuditorPortal';
import CertificateModal from './components/CertificateModal';

const API_BASE = 'http://localhost:8000';

export default function App() {
  const [activeTab, setActiveTab] = useState('news'); // 'news', 'profile', 'auditor'
  const [apiOnline, setApiOnline] = useState(false);
  const [users, setUsers] = useState([]);
  const [selectedUserId, setSelectedUserId] = useState('U1000');
  const [currentUser, setCurrentUser] = useState(null);
  const [activeCertificateModal, setActiveCertificateModal] = useState(null);
  const [externalCertToVerify, setExternalCertToVerify] = useState(null);

  // Poll API Health
  useEffect(() => {
    checkHealth();
    fetchUsers();
    const interval = setInterval(checkHealth, 5000);
    return () => clearInterval(interval);
  }, []);

  const checkHealth = async () => {
    try {
      const res = await fetch(`${API_BASE}/health`);
      setApiOnline(res.ok);
    } catch {
      setApiOnline(false);
    }
  };

  const fetchUsers = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/users`);
      if (res.ok) {
        const data = await res.json();
        setUsers(data);
        if (data.length > 0 && !selectedUserId) {
          setSelectedUserId(data[0].user_id);
        }
      }
    } catch (err) {
      console.error('Failed to fetch user list:', err);
    }
  };

  // Fetch selected user details
  useEffect(() => {
    if (selectedUserId) {
      fetchAgentDetails(selectedUserId);
    }
  }, [selectedUserId]);

  const fetchAgentDetails = async (uid) => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/users/${uid}`);
      if (res.ok) {
        setCurrentUser(await res.json());
      }
    } catch (err) {
      console.error('Failed to fetch user details:', err);
    }
  };

  const handleOpenCertificateModal = (cert) => {
    setActiveCertificateModal(cert);
  };

  const handleVerifyInAuditor = (cert) => {
    setExternalCertToVerify(cert);
    setActiveTab('auditor');
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      
      {/* Top Header Navigation Bar */}
      <header style={{
        background: 'rgba(9, 13, 22, 0.9)',
        backdropFilter: 'blur(16px)',
        borderBottom: '1px solid var(--border-color)',
        position: 'sticky',
        top: 0,
        zIndex: 100,
        padding: '16px 32px'
      }}>
        <div style={{ maxWidth: '1400px', margin: '0 auto', display: 'flex', flexWrap: 'wrap', gap: '16px', justifyContent: 'space-between', alignItems: 'center' }}>
          
          {/* Logo & Platform Name */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
            <div style={{
              width: '42px',
              height: '42px',
              borderRadius: '12px',
              background: 'linear-gradient(135deg, #06b6d4 0%, #6366f1 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 0 20px rgba(99, 102, 241, 0.4)'
            }}>
              <Newspaper size={24} color="#fff" />
            </div>

            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <h1 style={{ fontSize: '22px', fontWeight: '800' }} className="gradient-text">CryptoForget News</h1>
                <span style={{ fontSize: '10px', padding: '2px 8px', borderRadius: '10px', background: 'rgba(16, 185, 129, 0.15)', color: '#10b981', fontWeight: '700', border: '1px solid rgba(16, 185, 129, 0.3)' }}>
                  SISA Machine Unlearning Active
                </span>
              </div>
              <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                Adaptive Personalized Content & Cryptographically Verifiable Privacy Engine
              </p>
            </div>
          </div>

          {/* Navigation Controls */}
          <div style={{
            display: 'flex',
            background: '#111827',
            padding: '4px',
            borderRadius: '12px',
            border: '1px solid var(--border-color)'
          }}>
            <button
              onClick={() => setActiveTab('news')}
              style={{
                padding: '8px 18px',
                borderRadius: '8px',
                border: 'none',
                background: activeTab === 'news' ? 'linear-gradient(135deg, #6366f1 0%, #3b82f6 100%)' : 'transparent',
                color: activeTab === 'news' ? '#fff' : 'var(--text-muted)',
                fontWeight: '600',
                fontSize: '14px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                transition: 'all 0.2s'
              }}
            >
              <Newspaper size={16} /> News Feed
            </button>

            <button
              onClick={() => setActiveTab('profile')}
              style={{
                padding: '8px 18px',
                borderRadius: '8px',
                border: 'none',
                background: activeTab === 'profile' ? 'linear-gradient(135deg, #10b981 0%, #06b6d4 100%)' : 'transparent',
                color: activeTab === 'profile' ? '#090d16' : 'var(--text-muted)',
                fontWeight: '700',
                fontSize: '14px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                transition: 'all 0.2s'
              }}
            >
              <User size={16} /> Profile & Privacy Settings
            </button>

            <button
              onClick={() => setActiveTab('auditor')}
              style={{
                padding: '8px 18px',
                borderRadius: '8px',
                border: 'none',
                background: activeTab === 'auditor' ? '#374151' : 'transparent',
                color: activeTab === 'auditor' ? '#fff' : 'var(--text-muted)',
                fontWeight: '600',
                fontSize: '14px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                transition: 'all 0.2s'
              }}
            >
              <Lock size={16} /> Auditor Verifier
            </button>
          </div>

          {/* User Profile Switcher Header Widget */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <select
              value={selectedUserId}
              onChange={(e) => setSelectedUserId(e.target.value)}
              style={{
                padding: '6px 12px',
                borderRadius: '8px',
                background: '#1f2937',
                color: '#fff',
                border: '1px solid var(--border-color)',
                fontSize: '13px',
                fontWeight: '600',
                cursor: 'pointer'
              }}
            >
              {users.map((u) => (
                <option key={u.user_id} value={u.user_id}>
                  {u.user_id} - {u.name} {u.is_unlearned ? '🔒 [UNLEARNED]' : ''}
                </option>
              ))}
            </select>

            {/* Privacy Badge */}
            {currentUser && (
              <div style={{
                padding: '6px 12px',
                borderRadius: '16px',
                fontSize: '11px',
                fontWeight: '700',
                background: currentUser.is_unlearned ? 'rgba(244, 63, 94, 0.15)' : 'rgba(16, 185, 129, 0.15)',
                color: currentUser.is_unlearned ? '#f43f5e' : '#10b981',
                border: `1px solid ${currentUser.is_unlearned ? 'rgba(244, 63, 94, 0.3)' : 'rgba(16, 185, 129, 0.3)'}`
              }}>
                {currentUser.is_unlearned ? 'UNLEARNED' : 'ACTIVE'}
              </div>
            )}
          </div>

        </div>
      </header>

      {/* Main Content Body */}
      <main style={{ flex: 1, maxWidth: '1400px', width: '100%', margin: '0 auto', padding: '32px' }}>
        {activeTab === 'news' && (
          <NewsFeed
            currentUser={currentUser}
            onArticleClicked={() => fetchAgentDetails(selectedUserId)}
          />
        )}

        {activeTab === 'profile' && (
          <UserProfileSettings
            currentUser={currentUser}
            onUserUpdated={() => fetchAgentDetails(selectedUserId)}
            onInspectCertificate={handleOpenCertificateModal}
          />
        )}

        {activeTab === 'auditor' && (
          <AuditorPortal externalCertToVerify={externalCertToVerify} />
        )}
      </main>

      {/* Footer */}
      <footer style={{ borderTop: '1px solid var(--border-color)', padding: '24px 32px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '13px' }}>
        CryptoForget News Platform — Powered by SISA Exact Machine Unlearning & Cryptographic ECDSA Deletion Certificates
      </footer>

      {/* Certificate Inspector Modal */}
      {activeCertificateModal && (
        <CertificateModal
          certificate={activeCertificateModal}
          onClose={() => setActiveCertificateModal(null)}
          onVerifyInAuditor={handleVerifyInAuditor}
        />
      )}

    </div>
  );
}
