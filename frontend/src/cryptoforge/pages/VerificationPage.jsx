import { useCallback, useEffect, useState } from 'react';
import { api } from '../api/client';
import AuditLedgerPanel from '../../components/verification/AuditLedgerPanel';
import CertificateFields from '../../components/verification/CertificateFields';
import PasteVerify from '../../components/verification/PasteVerify';
import TamperTest from '../../components/verification/TamperTest';
import VerdictCard from '../../components/verification/VerdictCard';
import PipelineRail from '../../components/PipelineRail';
import { EmptyState, ErrorState } from '../../components/States';
import { useLatestCertificate } from '../../hooks/useLatestCertificate';
import { Link } from '../router/router';
import { useApp } from '../state/AppState';

export default function VerificationPage() {
  const { userId, personalization } = useApp();
  const cert = useLatestCertificate();
  const [verify, setVerify] = useState({ status: 'idle', result: null, error: null });

  const run = useCallback(async (certificate) => {
    setVerify({ status: 'running', result: null, error: null });
    try {
      const result = await api.verifyCertificate(certificate);
      setVerify({ status: 'done', result, error: null });
    } catch (err) {
      setVerify({ status: 'error', result: null, error: err.message });
    }
  }, []);

  // Verify automatically when the certificate loads.
  useEffect(() => {
    if (cert.status === 'ready') run(cert.certificate);
  }, [cert.status, cert.certificate, run]);

  const head = (
    <>
      <header className="cf-page-head">
        <h1>Cryptographic verification</h1>
        <p>
          The signed deletion certificate for <strong>{userId}</strong>, checked by the backend
          verifier, plus the tamper-evident audit ledger.
        </p>
      </header>
      <PipelineRail current="/verification" />
    </>
  );

  let body;
  if (cert.status === 'loading') {
    body = <div className="cf-skeleton" style={{ height: 260 }} aria-busy="true" />;
  } else if (cert.status === 'error') {
    body = <ErrorState title="Could not load the certificate" message={cert.error} onRetry={cert.reload} />;
  } else if (cert.status === 'none') {
    body = (
      <EmptyState
        title={`No deletion certificate for ${userId}`}
        action={
          personalization === 'on' ? (
            <Link to="/forget" className="cf-btn cf-btn--soft">
              Forget my data
            </Link>
          ) : null
        }
      >
        A certificate is issued when a forget request completes. You can still verify a pasted
        certificate and read the audit ledger below.
      </EmptyState>
    );
  } else {
    const certificate = cert.certificate;
    body = (
      <div className="cf-stack">
        <VerdictCard verify={verify} certificate={certificate} onRerun={() => run(certificate)} />
        <CertificateFields certificate={certificate} />

        <details className="cf-card cf-details cf-details--card">
          <summary>How to read this result</summary>
          <ul className="cf-list cf-list--plain">
            <li>
              The signature covers the certificate id, request id, user id, deletion path, both Merkle
              roots, both model hashes and the timestamp. Changing any of them makes verification
              fail.
            </li>
            <li>
              Each Merkle leaf is a SHA-256 hash of one user's click-history record in the unlearning
              engine. The inclusion proof shows the user's leaf was part of the old root.
            </li>
            <li>
              The model hashes are SHA-256 hashes of a version label plus the Merkle root. They are not
              hashes of serialized model weights.
            </li>
            <li>
              The verifier endpoint checks the signature and the inclusion proof to the old root. "Absent
              from new root" is a statement made by the issuer inside the certificate.
            </li>
            <li>The Merkle proof block is not part of the signed payload.</li>
          </ul>
        </details>

        <div className="cf-two">
          <TamperTest certificate={certificate} />
          <PasteVerify certificate={certificate} />
        </div>
      </div>
    );
  }

  return (
    <div>
      {head}
      {body}

      {cert.status === 'none' && (
        <div className="cf-stack cf-mt">
          <PasteVerify certificate={null} />
        </div>
      )}

      <div className="cf-mt">
        <AuditLedgerPanel highlightRequestId={cert.certificate?.request_id} />
      </div>
    </div>
  );
}