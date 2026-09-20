import { formatDateTime } from '../../cryptoforge/lib/time';
import { HashValue } from '../CopyButton';
import Icon from '../Icon';

function Row({ label, children }) {
  return (
    <div className="cf-kv__row">
      <dt>{label}</dt>
      <dd>{children}</dd>
    </div>
  );
}

export default function CertificateFields({ certificate }) {
  const proof = certificate.merkle_exclusion_proof || {};
  const steps = Array.isArray(proof.old_inclusion_proof) ? proof.old_inclusion_proof.length : 0;
  const rootsSame = certificate.old_merkle_root === certificate.new_merkle_root;

  const download = () => {
    const blob = new Blob([JSON.stringify(certificate, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${certificate.certificate_id}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <section className="cf-card cf-stack">
      <div className="cf-section-head">
        <h2>Deletion certificate</h2>
        <button type="button" className="cf-btn cf-btn--ghost" onClick={download}>
          Download JSON
        </button>
      </div>

      {rootsSame && (
        <div className="cf-notice cf-notice--warn">
          <Icon name="info" />
          <div>
            <strong>The old and new Merkle roots are identical.</strong> No committed history was
            removed in this run. The user had no history in the unlearning engine, or was already
            removed earlier in this backend session.
          </div>
        </div>
      )}

      <div>
        <h3 className="cf-h3">Identity</h3>
        <dl className="cf-kv">
          <Row label="Certificate id"><code>{certificate.certificate_id}</code></Row>
          <Row label="Request id"><code>{certificate.request_id}</code></Row>
          <Row label="User">{certificate.user_id}</Row>
          <Row label="Deletion path">{certificate.deletion_type}</Row>
          <Row label="Issued">
            <span title={certificate.timestamp}>{formatDateTime(certificate.timestamp)}</span>
          </Row>
        </dl>
      </div>

      <div>
        <h3 className="cf-h3">Merkle commitment</h3>
        <dl className="cf-kv">
          <Row label="Old root"><HashValue value={certificate.old_merkle_root} /></Row>
          <Row label="New root">
            <HashValue value={certificate.new_merkle_root} />{' '}
            <span className={`cf-chip ${rootsSame ? 'cf-chip--warn' : 'cf-chip--ok'}`}>
              {rootsSame ? 'Unchanged' : 'Changed'}
            </span>
          </Row>
          <Row label="Deleted leaf"><HashValue value={proof.deleted_leaf_hash} /></Row>
          <Row label="Inclusion proof to old root">
            {steps > 0 ? `${steps} step${steps === 1 ? '' : 's'}` : 'None in this certificate'}
          </Row>
          <Row label="Absent from new root">
            {proof.is_absent_in_new_root === undefined
              ? '—'
              : proof.is_absent_in_new_root
                ? 'Yes (stated by the issuer)'
                : 'No'}
          </Row>
          <Row label="Leaves in new tree">{proof.new_tree_leaf_count ?? '—'}</Row>
        </dl>
      </div>

      <div>
        <h3 className="cf-h3">Model hashes</h3>
        <dl className="cf-kv">
          <Row label="Before"><HashValue value={certificate.old_model_hash} /></Row>
          <Row label="After"><HashValue value={certificate.new_model_hash} /></Row>
        </dl>
      </div>

      <div>
        <h3 className="cf-h3">Signature</h3>
        <dl className="cf-kv">
          <Row label="ECDSA signature">
            <HashValue value={certificate.ecdsa_signature} head={24} tail={10} />
          </Row>
        </dl>
        {certificate.issuer_public_key_pem && (
          <details className="cf-details">
            <summary>Issuer public key</summary>
            <pre className="cf-pem">{certificate.issuer_public_key_pem}</pre>
          </details>
        )}
      </div>
    </section>
  );
}