# Privacy, Security, Data Governance and Deletion Policy

**Version:** 1.0  
**Date:** 2026-11-02  
**Purpose:** Engineering and research guidance; not legal advice.

## 1. Privacy principles

- Data minimization.
- Purpose limitation.
- Explicit opt-in for training.
- Separate consent for service storage and model training.
- Transparency and user control.
- Retention limitation.
- Security by design.
- Verifiable but privacy-preserving evidence.
- Accurate claims and no false assurance.

## 2. Data categories and purposes

| Data category | Purpose | Training eligible? | Suggested handling |
|---|---|---|---|
| Account identity | Authentication | No | Separate identity store |
| Chat content | Provide conversation history | Only with explicit opt-in | Encrypt, restrict access |
| Consent events | Record preference | No | Versioned audit record |
| Training record | Fine-tuning | Only within consent scope | Pseudonymous ID |
| Tombstone | Exclude requested data | No | Minimal metadata |
| Model checkpoint | Inference/training | May contain learned influence | Versioned, restricted |
| Certificate | Evidence of workflow | No | No PII |
| Security logs | Abuse/security | No | Redacted, retention-limited |

## 3. Consent model

Training consent must be:
- Off by default.
- Explicit, affirmative and unbundled.
- Purpose-specific.
- Time-stamped.
- Versioned with the privacy notice.
- Withdrawable.
- Enforced by the data pipeline, not merely by frontend state.

Record at least:
- pseudonymous subject ID
- consent event ID
- purpose
- scope
- policy version
- status (granted/withdrawn)
- effective timestamp
- collection context
- audit reference

Do not infer consent from continued use, account creation or acceptance of general terms.

## 4. Withdrawal versus deletion

These are separate operations:

### Withdraw training consent
- Stop future collection/use for training.
- Exclude eligible records from not-yet-started datasets.
- Fence active jobs and prevent stale jobs from committing affected data.
- Explain that previously trained models may still require a separate deletion/unlearning request.

### Delete data
- Identify all records and derivatives in scope.
- Tombstone immediately.
- Delete eligible raw/derived copies.
- Retrain affected model shards if data influenced a model.
- Retire old affected model artifacts.
- Apply backup retention/deletion process.
- Verify and issue certificate if policy passes.

## 5. Data lineage

Maintain a restricted lineage graph:

`subject pseudonym → record IDs → dataset version → shard → slice → checkpoint → model version → deployment`

Track derived artifacts:
- tokenized examples
- cached datasets
- preprocessing outputs
- evaluation exports
- embeddings (if ever introduced)
- checkpoints
- downstream model versions

If one user is represented in multiple shards, every affected shard must be handled.

## 6. Pre-tombstoning

Tombstone is a durable exclusion instruction. It is not erasure.

Requirements:
- Atomic request + tombstone transaction.
- Tombstone applied before expensive work.
- Training workers check current exclusion epoch before read and before commit.
- Dataset exports and retrieval must consult the exclusion manifest.
- Tombstones remain until the request is reconciled.
- Tombstones should contain minimal identifiers and no message content.
- Tombstone access is tightly restricted.

## 7. Deletion scope

Define and document scope for:
- Primary database.
- Object/file storage.
- Search indexes.
- Caches.
- Queues and dead-letter queues.
- Dataset files.
- Derived/tokenized data.
- Analytics exports.
- Logs.
- Model checkpoints and model versions.
- Backups and snapshots.
- Third-party subprocessors.

A completed certificate must state the policy scope. If backups are retained until expiry, disclose that and do not claim immediate erasure from every backup.

## 8. Model unlearning and residual risk

SISA retraining is an algorithmic method to reduce the influence of selected training records by retraining affected shard slices. It does not automatically guarantee that:
- all memorized information is absent,
- all downstream model copies are replaced,
- all exported checkpoints are deleted,
- no correlated information remains,
- model outputs can never reveal related facts.

Use clean retraining as a reference and empirical privacy attacks as tests. Phrase findings as measured evidence.

## 9. Threat model

### Assets
- Chat content.
- Identity mapping.
- Consent records.
- Training datasets.
- Model checkpoints.
- Signing keys.
- Deletion evidence.
- Public certificates.

### Adversaries
- Curious public verifier.
- Malicious user attempting to access another user's data.
- Compromised application account.
- Insider with excessive privileges.
- Malicious/buggy worker.
- Attacker modifying certificate payload.
- Attacker replaying stale training job.
- Attacker restoring old backup.

### Security controls
- Authentication and authorization.
- Least privilege.
- Encryption in transit and at rest.
- Secret manager for signing keys.
- Key rotation.
- Rate limiting.
- Audit logging.
- Job fencing.
- Immutable artifact versioning.
- Signed manifests.
- Backup restore reconciliation.
- Security tests and dependency scanning.

## 10. Certificate privacy

Public certificate should contain:
- random certificate ID
- request opaque reference
- issue/completion timestamps (coarse where needed)
- policy/schema version
- status
- broad operation categories
- evidence manifest digest
- signing key ID
- signature

Do not contain:
- name/email/phone
- account ID
- conversation text
- record IDs
- raw data hashes
- shard mapping if it could reveal sensitive operational information
- IP address or device identifiers

A public hash of a predictable email/message can be vulnerable to dictionary guessing. Do not publish unsalted hashes of low-entropy personal data.

## 11. Cryptographic protocol

- SHA-256 for digest.
- Ed25519 for digital signatures.
- RFC 8785 JSON Canonicalization Scheme or another specified canonical encoding.
- TLS for transport.
- Public key set published at a stable endpoint with key IDs.
- Private key held in KMS/HSM or protected secret store.
- Key rotation and revocation procedures.
- Transparency log for issuance/revocation events.

Signature verification and evidence-policy verification are separate checks.

## 12. Legal and regulatory review

Before any real-user deployment, obtain qualified legal/privacy review for the relevant jurisdictions. Consider applicable data protection law, notice/consent requirements, access/deletion rights, retention, processor contracts, cross-border transfers, breach response and children's data. Do not present this research prototype as automatically compliant with GDPR, India's DPDP Act or any other law solely because it implements consent and deletion features.

## 13. Incident response

- Revoke compromised signing key.
- Publish key status and affected certificate range.
- Stop new certificate issuance until key integrity restored.
- Preserve relevant audit evidence.
- Notify affected users/regulators as required by applicable law.
- Reissue certificates with new key where appropriate.
- Document root cause and remediation.

## 14. User-facing claims

Allowed:
“The platform reports that the deletion workflow completed under policy version X, and the signed evidence manifest passed the published verification checks.”

Not allowed without stronger proof:
“Cryptography proves your data is completely erased from every model and backup.”
“QR scan proves the model has forgotten you.”
“Mathematically guaranteed deletion” when only empirical testing was done.


## 15. Privacy/security controls for the three research contributions

### Merkle deletion transparency log
- Log only opaque certificate IDs, event type, timestamp, policy version and cryptographic commitments.
- Never log chat content, email, account IDs, raw record IDs or direct identifiers.
- Consider whether timestamps and event frequency can reveal sensitive behavior; use coarse public timestamps or delayed batching where appropriate.
- Signed tree heads and inclusion/consistency proofs must be independently verifiable.
- Log append-only; revocation is a new event, not deletion/edit of old event.
- Publish a clear trust model: users trust the log operator's signing key unless independently witnessed/monitored.
- A Merkle proof establishes log inclusion/consistency, not physical erasure or model forgetting.

### Training-job race prevention
- Treat stale training workers as a privacy threat: they may publish artifacts trained on data after a deletion request.
- Tombstone and epoch increment must be atomic.
- Worker must revalidate at commit time, not just at job start.
- Use fencing tokens to prevent delayed workers from committing after lease expiry.
- Dataset manifest digest and epoch must be included in model/checkpoint provenance.
- Restore/recovery must preserve the highest known exclusion epoch so an old backup cannot silently roll it back.
- Test network partition, process pause, worker crash and delayed commit scenarios.

### Cost-aware SISA configuration
- Research optimization must not weaken consent or deletion guarantees to save compute.
- A faster configuration is unacceptable if it leaves affected shards untouched or publishes stale models.
- Include storage retention, model utility, forgetting and inference overhead in the objective.
- Keep a minimum verification policy constant across configurations so results remain comparable.
