import React, { useState, useEffect } from 'react';
import { 
  ShieldCheck, Lock, FileCheck, Search, Activity, 
  CheckCircle2, XCircle, Clock, Upload, ArrowRight, Zap 
} from 'lucide-react';

const API_BASE = 'http://localhost:8000';

export default function AuditorPortal({ externalCertToVerify }) {
  const [auditData, setAuditData] = useState(null);
  const [miaData, setMiaData] = useState(null);
  const [certInput, setCertInput] = useState('');
  const [verificationResult, setVerificationResult] = useState(null);
  const [verifying, setVerifying] = useState(false);

  useEffect(() => {
    fetchAuditTrail();
    fetchMiaBenchmark();
  }, []);

  useEffect(() => {
    if (externalCertToVerify) {
      setCertInput(JSON.stringify(externalCertToVerify, null, 2));
      handleVerifyCertJSON(JSON.stringify(externalCertToVerify, null, 2));
    }
  }, [externalCertToVerify]);

  const fetchAuditTrail = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/auditor/audit-trail`);
      if (res.ok) {
        setAuditData(await res.json());
      }
    } catch (err) {
      console.error('Failed to fetch audit trail:', err);
    }
  };

  const fetchMiaBenchmark = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/auditor/mia-benchmark`);
      if (res.ok) {
        setMiaData(await res.json());
      }
    } catch (err) {
      console.error('Failed to fetch MIA benchmark:', err);
    }
  };

  const handleVerifyCertJSON = async (jsonText) => {
    setVerifying(true);
    setVerificationResult(null);

    try {
      const certObj = JSON.parse(jsonText || certInput);
      const res = await fetch(`${API_BASE}/api/v1/verify-certificate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ certificate: certObj })
      });

      if (res.ok) {
        const data = await res.json();
        setVerificationResult(data);
      } else {
        setVerificationResult({
          is_valid: false,
          message: 'Certificate JSON validation failed.',
          verification_time_ms: 0.0
        });
      }
    } catch (err) {
      setVerificationResult({
        is_valid: false,
        message: 'Invalid JSON format or malformed certificate.',
        verification_time_ms: 0.0
      });
    } finally {
      setVerifying(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      
      {/* Top Banner: Independent Deletion Certificate Offline Validator */}
      <div className="glass-card" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
        <div>
          <h3 style={{ fontSize: '18px', fontWeight: '700' }} className="gradient-text">
            Independent Deletion Certificate Offline Validator
          </h3>
          <p style={{ fontSize: '13px', color: 'var(--text-muted)', marginTop: '2px' }}>
            Verifies ECDSA SECP256k1 digital signatures & Merkle exclusion proofs in &lt; 100ms
          </p>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(350px, 1fr))', gap: '20px' }}>
          <div>
            <label style={{ fontSize: '12px', fontWeight: '600', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
              Paste Certificate JSON Payload
            </label>
            <textarea
              value={certInput}
              onChange={(e) => setCertInput(e.target.value)}
              placeholder='Paste signed certificate JSON here...'
              rows={8}
              style={{
                width: '100%',
                marginTop: '6px',
                padding: '12px',
                borderRadius: '8px',
                background: '#090d16',
                color: '#38bdf8',
                border: '1px solid var(--border-color)',
                fontFamily: 'var(--font-mono)',
                fontSize: '12px',
                outline: 'none'
              }}
            />

            <button
              onClick={() => handleVerifyCertJSON()}
              disabled={verifying || !certInput.trim()}
              style={{
                marginTop: '12px',
                padding: '12px 24px',
                borderRadius: '8px',
                background: 'linear-gradient(135deg, #10b981 0%, #06b6d4 100%)',
                color: '#090d16',
                border: 'none',
                fontWeight: '700',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}
            >
              {verifying ? <Zap className="animate-spin" size={16} /> : <ShieldCheck size={16} />}
              Verify ECDSA Signature & Merkle Proof
            </button>
          </div>

          {/* Verification Result Display */}
          <div style={{ padding: '20px', borderRadius: '12px', background: '#1f2937', border: '1px solid var(--border-color)', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
            {verificationResult ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  {verificationResult.is_valid ? (
                    <CheckCircle2 size={28} color="#10b981" />
                  ) : (
                    <XCircle size={28} color="#f43f5e" />
                  )}
                  <div>
                    <div style={{ fontSize: '16px', fontWeight: '700', color: verificationResult.is_valid ? '#10b981' : '#f43f5e' }}>
                      {verificationResult.is_valid ? 'VALID DELETION CERTIFICATE' : 'INVALID / TAMPERED CERTIFICATE'}
                    </div>
                    <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                      Verification Latency: <strong>{verificationResult.verification_time_ms} ms</strong> (Target: &lt; 100ms)
                    </div>
                  </div>
                </div>

                <div style={{ fontSize: '13px', color: '#d1d5db', padding: '12px', background: '#090d16', borderRadius: '8px' }}>
                  {verificationResult.message}
                </div>
              </div>
            ) : (
              <div style={{ textAlign: 'center', color: 'var(--text-muted)' }}>
                <FileCheck size={36} style={{ margin: '0 auto 12px', opacity: 0.5 }} />
                <p style={{ fontSize: '13px' }}>Paste a certificate JSON and click Verify to inspect ECDSA cryptographic proofs.</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* MIA Privacy Benchmark Display */}
      <div className="glass-card" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
        <div>
          <h3 style={{ fontSize: '18px', fontWeight: '700' }} className="gradient-text-emerald">
            Membership Inference Attack (MIA) Privacy Benchmark
          </h3>
          <p style={{ fontSize: '13px', color: 'var(--text-muted)', marginTop: '2px' }}>
            Measures attacker prediction accuracy. Target: unlearned privacy converges toward ~50% (random guessing).
          </p>
        </div>

        {miaData && (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '16px' }}>
            
            <div style={{ padding: '16px', borderRadius: '12px', background: '#1f2937', border: '1px solid var(--border-color)' }}>
              <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Trained User MIA Attack Success</div>
              <div style={{ fontSize: '24px', fontWeight: '800', color: '#f43f5e', marginTop: '4px' }}>
                {(miaData.trained_population_mia_accuracy * 100).toFixed(1)}%
              </div>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px' }}>High detectability before unlearning</div>
            </div>

            <div style={{ padding: '16px', borderRadius: '12px', background: '#1f2937', border: '1px solid #10b981' }}>
              <div style={{ fontSize: '12px', color: '#10b981', fontWeight: '600' }}>Unlearned User MIA Success</div>
              <div style={{ fontSize: '24px', fontWeight: '800', color: '#10b981', marginTop: '4px' }}>
                {(miaData.unlearned_population_mia_accuracy * 100).toFixed(1)}%
              </div>
              <div style={{ fontSize: '11px', color: '#10b981', marginTop: '4px' }}>Converged to random guessing baseline (~50%)</div>
            </div>

            <div style={{ padding: '16px', borderRadius: '12px', background: '#1f2937', border: '1px solid var(--border-color)' }}>
              <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Target Benchmark Baseline</div>
              <div style={{ fontSize: '24px', fontWeight: '800', color: '#06b6d4', marginTop: '4px' }}>
                {(miaData.target_random_guessing_baseline * 100).toFixed(1)}%
              </div>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px' }}>Ideal zero-knowledge privacy bound</div>
            </div>

          </div>
        )}
      </div>

      {/* Append-Only Hash-Chained Audit Ledger Table */}
      <div className="glass-card" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h3 style={{ fontSize: '18px', fontWeight: '700' }} className="gradient-text">
              Cryptographic Hash-Chained Audit Ledger
            </h3>
            <p style={{ fontSize: '13px', color: 'var(--text-muted)', marginTop: '2px' }}>
              Tamper-evident append-only ledger recording all data ingestion & unlearning events
            </p>
          </div>

          <div style={{
            padding: '6px 14px',
            borderRadius: '20px',
            fontSize: '12px',
            fontWeight: '600',
            background: auditData?.ledger_integrity_valid ? 'rgba(16, 185, 129, 0.15)' : 'rgba(244, 63, 94, 0.15)',
            color: auditData?.ledger_integrity_valid ? '#10b981' : '#f43f5e',
            border: `1px solid ${auditData?.ledger_integrity_valid ? 'rgba(16, 185, 129, 0.3)' : 'rgba(244, 63, 94, 0.3)'}`,
            display: 'flex',
            alignItems: 'center',
            gap: '6px'
          }}>
            <Lock size={14} />
            {auditData?.ledger_integrity_valid ? 'CHAIN INTEGRITY: VERIFIED' : 'TAMPER ALERT'}
          </div>
        </div>

        {auditData && auditData.blocks && (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px', textAlign: 'left' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-color)', color: 'var(--text-muted)' }}>
                  <th style={{ padding: '12px' }}>Block #</th>
                  <th style={{ padding: '12px' }}>Timestamp</th>
                  <th style={{ padding: '12px' }}>Action</th>
                  <th style={{ padding: '12px' }}>Logged Model Eval Metrics</th>
                  <th style={{ padding: '12px' }}>Payload Hash</th>
                  <th style={{ padding: '12px' }}>Previous Hash</th>
                  <th style={{ padding: '12px' }}>Current Hash</th>
                </tr>
              </thead>
              <tbody>
                {auditData.blocks.map((block) => (
                  <tr key={block.block_id} style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.05)' }}>
                    <td style={{ padding: '12px', fontWeight: '700', color: '#818cf8' }}>#{block.block_id}</td>
                    <td style={{ padding: '12px', color: 'var(--text-muted)' }}>{block.timestamp ? new Date(block.timestamp).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata', hour12: true }) + ' IST' : 'N/A'}</td>
                    <td style={{ padding: '12px', fontWeight: '600', color: '#10b981' }}>{block.action}</td>
                    <td style={{ padding: '12px' }}>
                      {block.metrics ? (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '2px', fontSize: '11px', fontFamily: 'var(--font-mono)' }}>
                          <span style={{ color: '#10b981' }}>AUC: {block.metrics.pre_unlearn_auc} &#8594; {block.metrics.post_unlearn_auc}</span>
                          <span style={{ color: '#38bdf8' }}>MRR: {block.metrics.mrr} | NDCG@5: {block.metrics.ndcg_5}</span>
                          <span style={{ color: '#818cf8' }}>MIA Privacy Rate: {(block.metrics.mia_attack_success_rate * 100).toFixed(1)}% (Target ~50%)</span>
                          <span style={{ color: '#f59e0b' }}>Retrain: {block.metrics.retrain_duration_ms} ms</span>
                        </div>
                      ) : (
                        <span style={{ color: 'var(--text-muted)', fontStyle: 'italic' }}>Genesis / System Ledger Event</span>
                      )}
                    </td>
                    <td style={{ padding: '12px', fontFamily: 'var(--font-mono)', color: '#38bdf8' }}>{block.payload_hash.slice(0, 12)}...</td>
                    <td style={{ padding: '12px', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>{block.prev_hash.slice(0, 12)}...</td>
                    <td style={{ padding: '12px', fontFamily: 'var(--font-mono)', color: '#a78bfa' }}>{block.curr_hash.slice(0, 12)}...</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

    </div>
  );
}
