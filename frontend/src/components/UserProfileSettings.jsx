import React, { useState, useEffect } from 'react';
import { 
  User, Shield, ShieldCheck, Trash2, CheckCircle2, 
  FileCheck, Download, Zap, AlertCircle, RefreshCw, Lock, Key
} from 'lucide-react';

const API_BASE = 'http://localhost:8000';

export default function UserProfileSettings({ currentUser, onUserUpdated, onInspectCertificate }) {
  const [deletionType, setDeletionType] = useState('Path B');
  const [unlearningStatus, setUnlearningStatus] = useState('idle'); // idle, processing, completed
  const [unlearningStep, setUnlearningStep] = useState(0);
  const [certificate, setCertificate] = useState(null);
  const [verificationResult, setVerificationResult] = useState(null);
  const [verifying, setVerifying] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  // Fetch existing certificate if already unlearned
  useEffect(() => {
    if (currentUser?.is_unlearned) {
      fetchUserCertificate(currentUser.user_id);
    }
  }, [currentUser]);

  const fetchUserCertificate = async (uid) => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/certificate/${uid}`);
      if (res.ok) {
        setCertificate(await res.json());
      }
    } catch (err) {
      console.error('No certificate found:', err);
    }
  };

  const handleRevokeConsent = async () => {
    setUnlearningStatus('processing');
    setUnlearningStep(1);
    setErrorMessage('');
    setVerificationResult(null);

    // Step 1 animation
    setTimeout(() => setUnlearningStep(2), 600);

    try {
      const res = await fetch(`${API_BASE}/api/v1/delete-user`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: currentUser.user_id,
          deletion_type: deletionType
        })
      });

      if (res.ok) {
        setUnlearningStep(3);
        const data = await res.json();
        
        setTimeout(() => {
          setUnlearningStep(4);
          setCertificate(data.certificate);
          setUnlearningStatus('completed');
          if (onUserUpdated) onUserUpdated();
        }, 500);

      } else {
        const errData = await res.json();
        setErrorMessage(errData.detail || 'Unlearning execution failed.');
        setUnlearningStatus('idle');
      }
    } catch (err) {
      setErrorMessage('Communication error with unlearning backend.');
      setUnlearningStatus('idle');
    }
  };

  const handleVerifyCertificate = async () => {
    if (!certificate) return;
    setVerifying(true);
    try {
      const res = await fetch(`${API_BASE}/api/v1/verify-certificate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ certificate })
      });
      if (res.ok) {
        setVerificationResult(await res.json());
      }
    } catch (err) {
      console.error('Failed to verify certificate:', err);
    } finally {
      setVerifying(false);
    }
  };

  const handleDownloadCertificate = () => {
    if (!certificate) return;
    const blob = new Blob([JSON.stringify(certificate, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `CryptoForget_Certificate_${certificate.certificate_id}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  if (!currentUser) return null;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
      
      {/* User Account Info Header */}
      <div className="glass-card" style={{ padding: '28px', display: 'flex', flexWrap: 'wrap', gap: '24px', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
          <div style={{
            width: '64px',
            height: '64px',
            borderRadius: '16px',
            background: 'linear-gradient(135deg, #6366f1 0%, #06b6d4 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#fff',
            fontSize: '24px',
            fontWeight: '800'
          }}>
            {currentUser.name ? currentUser.name[0] : 'U'}
          </div>

          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <h2 style={{ fontSize: '22px', fontWeight: '800', color: '#f9fafb' }}>{currentUser.name}</h2>
              <span style={{ fontSize: '11px', padding: '2px 8px', borderRadius: '10px', background: 'rgba(99, 102, 241, 0.2)', color: '#818cf8', fontWeight: '700', border: '1px solid rgba(99, 102, 241, 0.4)' }}>
                ID: {currentUser.user_id}
              </span>
            </div>
            <p style={{ fontSize: '14px', color: 'var(--text-muted)', marginTop: '2px' }}>{currentUser.email}</p>
          </div>
        </div>

        {/* Status Badge */}
        <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
          <div style={{
            padding: '10px 18px',
            borderRadius: '24px',
            fontSize: '13px',
            fontWeight: '700',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            background: currentUser.is_unlearned ? 'rgba(244, 63, 94, 0.15)' : 'rgba(16, 185, 129, 0.15)',
            color: currentUser.is_unlearned ? '#f43f5e' : '#10b981',
            border: `1px solid ${currentUser.is_unlearned ? 'rgba(244, 63, 94, 0.3)' : 'rgba(16, 185, 129, 0.3)'}`
          }}>
            <span style={{ width: '10px', height: '10px', borderRadius: '50%', background: currentUser.is_unlearned ? '#f43f5e' : '#10b981' }}></span>
            {currentUser.is_unlearned ? 'MODEL CONSENT REVOKED & UNLEARNED' : 'DATA ACTIVE IN MODEL TRAINING'}
          </div>
        </div>
      </div>

      {errorMessage && (
        <div style={{ padding: '16px', borderRadius: '12px', background: 'rgba(244, 63, 94, 0.15)', border: '1px solid rgba(244, 63, 94, 0.3)', color: '#f43f5e', display: 'flex', alignItems: 'center', gap: '12px' }}>
          <AlertCircle size={20} />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Main Privacy & Model Retraining Settings Box */}
      <div className="glass-card" style={{ padding: '28px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
        
        <div>
          <h3 style={{ fontSize: '20px', fontWeight: '800' }} className="gradient-text-emerald">
            Privacy Settings & Model Consent Control
          </h3>
          <p style={{ fontSize: '14px', color: 'var(--text-muted)', marginTop: '4px' }}>
            Exercising your GDPR Article 17 "Right to be Forgotten". Stop your data from being used in model retraining.
          </p>
        </div>

        {/* Privacy Status Explanation */}
        <div style={{
          padding: '20px',
          borderRadius: '12px',
          background: '#1f2937',
          border: '1px solid var(--border-color)',
          display: 'flex',
          gap: '16px',
          alignItems: 'flex-start'
        }}>
          <div style={{ padding: '10px', borderRadius: '10px', background: currentUser.is_unlearned ? 'rgba(244, 63, 94, 0.2)' : 'rgba(16, 185, 129, 0.2)', color: currentUser.is_unlearned ? '#f43f5e' : '#10b981' }}>
            {currentUser.is_unlearned ? <Lock size={24} /> : <ShieldCheck size={24} />}
          </div>

          <div>
            <h4 style={{ fontSize: '15px', fontWeight: '700', color: '#f9fafb' }}>
              {currentUser.is_unlearned ? 'Personal Data Influence Cryptographically Erased' : 'Active Model Personalization'}
            </h4>
            <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginTop: '4px', lineHeight: '1.5' }}>
              {currentUser.is_unlearned ? (
                'Your reading history and preferences have been permanently removed from SISA Shard #2 model parameters. A verifiable signed ECDSA deletion certificate has been issued.'
              ) : (
                `Your interaction behavior is stored in SISA Shard #${currentUser.shard_id} and actively used to personalize news recommendations. You can revoke consent below to trigger machine unlearning.`
              )}
            </p>
          </div>
        </div>

        {!currentUser.is_unlearned && (
          <>
            {/* Unlearning Path Choice */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <label style={{ fontSize: '12px', fontWeight: '700', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Select Unlearning Execution Strategy
              </label>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '16px' }}>
                <div
                  onClick={() => setDeletionType('Path B')}
                  style={{
                    padding: '16px',
                    borderRadius: '12px',
                    border: `2px solid ${deletionType === 'Path B' ? '#6366f1' : 'var(--border-color)'}`,
                    background: deletionType === 'Path B' ? 'rgba(99, 102, 241, 0.15)' : '#1f2937',
                    cursor: 'pointer'
                  }}
                >
                  <div style={{ fontSize: '15px', fontWeight: '700', color: deletionType === 'Path B' ? '#818cf8' : '#fff' }}>
                    Path B — Post-Training SISA Retraining (Recommended)
                  </div>
                  <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '6px', lineHeight: '1.4' }}>
                    Immediately purges user data from SISA Shard #{currentUser.shard_id} and retrains that shard only (21.3x faster than full model retraining).
                  </div>
                </div>

                <div
                  onClick={() => setDeletionType('Path A')}
                  style={{
                    padding: '16px',
                    borderRadius: '12px',
                    border: `2px solid ${deletionType === 'Path A' ? '#10b981' : 'var(--border-color)'}`,
                    background: deletionType === 'Path A' ? 'rgba(16, 185, 129, 0.15)' : '#1f2937',
                    cursor: 'pointer'
                  }}
                >
                  <div style={{ fontSize: '15px', fontWeight: '700', color: deletionType === 'Path A' ? '#10b981' : '#fff' }}>
                    Path A — Pre-Training Tombstoning
                  </div>
                  <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '6px', lineHeight: '1.4' }}>
                    Flags user records as tombstoned in feature store and excludes them from future retraining runs.
                  </div>
                </div>
              </div>
            </div>

            {/* Main Revoke Consent Button */}
            <button
              onClick={handleRevokeConsent}
              disabled={unlearningStatus === 'processing'}
              style={{
                padding: '18px',
                borderRadius: '14px',
                background: 'linear-gradient(135deg, #f43f5e 0%, #e11d48 100%)',
                color: '#fff',
                border: 'none',
                fontSize: '16px',
                fontWeight: '800',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '12px',
                boxShadow: '0 10px 30px -5px rgba(244, 63, 94, 0.5)'
              }}
            >
              {unlearningStatus === 'processing' ? (
                <>
                  <RefreshCw className="animate-spin" size={22} />
                  Executing Unlearning on SISA Shard #{currentUser.shard_id}...
                </>
              ) : (
                <>
                  <Trash2 size={22} />
                  Stop Using My Data & Unlearn Model Weights ({deletionType})
                </>
              )}
            </button>
          </>
        )}

        {/* Live Step Progress Bar during Unlearning */}
        {unlearningStatus === 'processing' && (
          <div style={{ padding: '20px', borderRadius: '12px', background: '#090d16', border: '1px solid #6366f1', display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <div style={{ fontSize: '13px', fontWeight: '700', color: '#818cf8', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Zap className="animate-spin" size={16} /> Unlearning Pipeline Active
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', fontSize: '12px' }}>
              <div style={{ color: unlearningStep >= 1 ? '#10b981' : 'var(--text-muted)' }}>1. Isolating Shard #{currentUser.shard_id}</div>
              <div style={{ color: unlearningStep >= 2 ? '#10b981' : 'var(--text-muted)' }}>2. Selective Shard Retraining</div>
              <div style={{ color: unlearningStep >= 3 ? '#10b981' : 'var(--text-muted)' }}>3. SHA-256 Merkle Root Update</div>
              <div style={{ color: unlearningStep >= 4 ? '#10b981' : 'var(--text-muted)' }}>4. Signing ECDSA Certificate</div>
            </div>
          </div>
        )}

      </div>

      {/* Official Cryptographic Signed Deletion Certificate Card */}
      {certificate && (
        <div className="glass-card" style={{ padding: '28px', border: '1px solid rgba(16, 185, 129, 0.4)', display: 'flex', flexDirection: 'column', gap: '20px' }}>
          
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--border-color)', paddingBottom: '16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <div style={{ padding: '10px', borderRadius: '12px', background: 'rgba(16, 185, 129, 0.2)', color: '#10b981' }}>
                <Key size={24} />
              </div>
              <div>
                <h3 style={{ fontSize: '18px', fontWeight: '800', color: '#10b981' }}>
                  Official Cryptographic Deletion Certificate
                </h3>
                <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                  Mathematically Verifiable Proof of Data Removal
                </p>
              </div>
            </div>

            <span style={{ fontSize: '11px', padding: '4px 12px', borderRadius: '12px', background: 'rgba(16, 185, 129, 0.15)', color: '#10b981', fontWeight: '700', border: '1px solid rgba(16, 185, 129, 0.3)' }}>
              ECDSA SECP256k1 SIGNED
            </span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px', fontSize: '13px' }}>
            <div style={{ padding: '14px', borderRadius: '10px', background: '#1f2937' }}>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>CERTIFICATE ID</div>
              <div style={{ fontSize: '14px', fontWeight: '700', color: '#06b6d4', fontFamily: 'var(--font-mono)', marginTop: '4px' }}>{certificate.certificate_id}</div>
            </div>

            <div style={{ padding: '14px', borderRadius: '10px', background: '#1f2937' }}>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>OLD MERKLE ROOT</div>
              <div style={{ fontSize: '12px', fontFamily: 'var(--font-mono)', color: '#9ca3af', marginTop: '4px' }}>{certificate.old_merkle_root.slice(0, 20)}...</div>
            </div>

            <div style={{ padding: '14px', borderRadius: '10px', background: '#1f2937' }}>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>NEW MERKLE ROOT</div>
              <div style={{ fontSize: '12px', fontFamily: 'var(--font-mono)', color: '#10b981', marginTop: '4px' }}>{certificate.new_merkle_root.slice(0, 20)}...</div>
            </div>

            <div style={{ padding: '14px', borderRadius: '10px', background: '#1f2937' }}>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>ECDSA SIGNATURE</div>
              <div style={{ fontSize: '12px', fontFamily: 'var(--font-mono)', color: '#a78bfa', marginTop: '4px' }}>{certificate.ecdsa_signature.slice(0, 20)}...</div>
            </div>
          </div>

          {/* Verification Results */}
          {verificationResult && (
            <div style={{ padding: '14px', borderRadius: '10px', background: 'rgba(16, 185, 129, 0.15)', border: '1px solid rgba(16, 185, 129, 0.3)', color: '#10b981', fontSize: '13px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <CheckCircle2 size={18} />
                <span>{verificationResult.message}</span>
              </div>
              <span style={{ fontSize: '12px', fontWeight: '700', fontFamily: 'var(--font-mono)' }}>
                {verificationResult.verification_time_ms} ms
              </span>
            </div>
          )}

          {/* Actions */}
          <div style={{ display: 'flex', gap: '14px', justifyContent: 'flex-end', paddingTop: '12px', borderTop: '1px solid var(--border-color)' }}>
            <button
              onClick={handleDownloadCertificate}
              style={{
                padding: '10px 18px',
                borderRadius: '8px',
                background: '#1f2937',
                color: '#fff',
                border: '1px solid var(--border-color)',
                fontSize: '13px',
                fontWeight: '600',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}
            >
              <Download size={16} /> Download Certificate (JSON)
            </button>

            <button
              onClick={handleVerifyCertificate}
              disabled={verifying}
              style={{
                padding: '10px 20px',
                borderRadius: '8px',
                background: 'linear-gradient(135deg, #10b981 0%, #06b6d4 100%)',
                color: '#090d16',
                border: 'none',
                fontSize: '13px',
                fontWeight: '700',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}
            >
              {verifying ? <RefreshCw className="animate-spin" size={16} /> : <Zap size={16} />}
              Verify Cryptographic Signature
            </button>
          </div>

        </div>
      )}

    </div>
  );
}
