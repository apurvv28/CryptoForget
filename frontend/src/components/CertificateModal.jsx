import React, { useState } from 'react';
import { X, CheckCircle2, Copy, ShieldCheck, FileCheck, Zap } from 'lucide-react';

export default function CertificateModal({ certificate, onClose, onVerifyInAuditor }) {
  const [copied, setCopied] = useState(false);

  if (!certificate) return null;

  const handleCopyJSON = () => {
    navigator.clipboard.writeText(JSON.stringify(certificate, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      background: 'rgba(0, 0, 0, 0.8)',
      backdropFilter: 'blur(8px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000,
      padding: '20px'
    }}>
      <div className="glass-card" style={{
        maxWidth: '750px',
        width: '100%',
        maxHeight: '90vh',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
        border: '1px solid rgba(16, 185, 129, 0.4)'
      }}>
        
        {/* Modal Header */}
        <div style={{
          padding: '20px 24px',
          borderBottom: '1px solid var(--border-color)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          background: 'rgba(16, 185, 129, 0.08)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <ShieldCheck size={24} color="#10b981" />
            <div>
              <h3 style={{ fontSize: '18px', fontWeight: '700', color: '#10b981' }}>
                Signed Deletion Certificate
              </h3>
              <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                Verifiable ECDSA Signature & Merkle Exclusion Proof
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', padding: '4px' }}
          >
            <X size={20} />
          </button>
        </div>

        {/* Modal Body */}
        <div style={{ padding: '24px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', fontSize: '13px' }}>
            <div style={{ padding: '12px', borderRadius: '8px', background: '#1f2937' }}>
              <span style={{ color: 'var(--text-muted)', fontSize: '11px', display: 'block' }}>CERTIFICATE ID</span>
              <strong style={{ color: '#06b6d4', fontFamily: 'var(--font-mono)' }}>{certificate.certificate_id}</strong>
            </div>

            <div style={{ padding: '12px', borderRadius: '8px', background: '#1f2937' }}>
              <span style={{ color: 'var(--text-muted)', fontSize: '11px', display: 'block' }}>USER ID & TYPE</span>
              <strong style={{ color: '#f3f4f6' }}>{certificate.user_id} ({certificate.deletion_type})</strong>
            </div>

            <div style={{ padding: '12px', borderRadius: '8px', background: '#1f2937' }}>
              <span style={{ color: 'var(--text-muted)', fontSize: '11px', display: 'block' }}>PRE-DELETION MERKLE ROOT</span>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: '#9ca3af' }}>{certificate.old_merkle_root.slice(0, 24)}...</span>
            </div>

            <div style={{ padding: '12px', borderRadius: '8px', background: '#1f2937' }}>
              <span style={{ color: 'var(--text-muted)', fontSize: '11px', display: 'block' }}>POST-DELETION MERKLE ROOT</span>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: '11px', color: '#10b981' }}>{certificate.new_merkle_root.slice(0, 24)}...</span>
            </div>
          </div>

          <div>
            <label style={{ fontSize: '12px', fontWeight: '600', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
              Full Certificate Payload JSON
            </label>
            <pre style={{
              marginTop: '6px',
              padding: '14px',
              borderRadius: '8px',
              background: '#090d16',
              color: '#38bdf8',
              fontFamily: 'var(--font-mono)',
              fontSize: '11px',
              maxHeight: '220px',
              overflow: 'auto',
              border: '1px solid var(--border-color)'
            }}>
              {JSON.stringify(certificate, null, 2)}
            </pre>
          </div>

        </div>

        {/* Modal Footer */}
        <div style={{
          padding: '16px 24px',
          borderTop: '1px solid var(--border-color)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          background: '#111827'
        }}>
          <button
            onClick={handleCopyJSON}
            style={{
              padding: '10px 16px',
              borderRadius: '8px',
              background: '#1f2937',
              color: '#fff',
              border: '1px solid var(--border-color)',
              fontWeight: '600',
              fontSize: '13px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px'
            }}
          >
            {copied ? <CheckCircle2 size={16} color="#10b981" /> : <Copy size={16} />}
            {copied ? 'Copied to Clipboard!' : 'Copy Certificate JSON'}
          </button>

          <button
            onClick={() => {
              onVerifyInAuditor(certificate);
              onClose();
            }}
            style={{
              padding: '10px 20px',
              borderRadius: '8px',
              background: 'linear-gradient(135deg, #10b981 0%, #06b6d4 100%)',
              color: '#090d16',
              border: 'none',
              fontWeight: '700',
              fontSize: '13px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px'
            }}
          >
            <Zap size={16} />
            Verify in Auditor Portal
          </button>
        </div>

      </div>
    </div>
  );
}
