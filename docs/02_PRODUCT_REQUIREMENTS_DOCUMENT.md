# Product Requirements Document (PRD)

**Product:** Privacy-first AI Chatbot with User-Controlled Training and Verifiable Deletion  
**Version:** 1.0  
**Date:** 2026-11-02  
**Status:** Proposed research prototype

## 1. Product vision

Provide a familiar conversational AI experience while making training consent, data deletion and model unlearning understandable and auditable to users.

The product should make three concepts visible:
- What data is stored.
- Whether data is eligible for model training.
- What happened after a deletion request.

The product is a research prototype, not a claim of legally certified or mathematically perfect erasure.

## 2. Target users

### Primary
- Individual chatbot users who want control over training use of their conversations.
- Researchers evaluating machine unlearning and deletion evidence.

### Secondary
- Independent certificate verifiers.
- System administrators/research operators.

## 3. Product principles

1. Training opt-in is explicit and off by default.
2. Service storage and training consent are separate choices.
3. Withdrawal stops future training use immediately.
4. Deletion is an asynchronous, visible workflow.
5. No completed certificate before all required checks pass.
6. Public verification reveals no personal content.
7. Claims are limited to evidence actually collected.
8. Accessibility and plain-language explanations are required.

## 4. Functional requirements

### FR-01 Chat
- User can create and access a conversation.
- User can send text messages and receive model responses.
- Interface shows loading/error state.
- Chat history follows retention settings.
- Inference uses a pinned model version.

### FR-02 Account and authentication
- User can register, sign in, sign out and request account deletion.
- Session cookies are secure, HttpOnly and SameSite where applicable.
- Passwords are stored using a suitable password hashing scheme, never plaintext.
- Administrative routes require role-based access.

### FR-03 Consent
- Training consent is off by default.
- UI explains data categories, training purpose, duration and withdrawal.
- Consent changes create immutable/versioned consent events.
- Consent is scoped by purpose and policy version.
- User can withdraw consent.
- Withdrawal prevents new records entering training immediately.
- Consent is not bundled with terms acceptance.

### FR-04 Data inventory
- User can see categories of retained data and retention periods.
- User can distinguish conversation storage from training use.
- User can see whether any eligible records have been used in a model version.
- Do not reveal internal security-sensitive identifiers.

### FR-05 Deletion
- User can request deletion of selected conversations or all eligible data.
- Request is authenticated and idempotent.
- User receives a request ID and immediate acknowledgement.
- User sees states: received, excluded, source deletion, unlearning, verification, completed/failed.
- User can cancel only before the irreversible stage if policy permits; cancellation must not restore consent.
- Failure is communicated honestly.

### FR-06 Pre-tombstoning
- Tombstone transaction occurs before background retraining.
- Tombstoned records cannot be included in new datasets or jobs.
- Jobs started before tombstone must revalidate exclusion epoch before committing.
- Tombstone is durable and auditable.

### FR-07 SISA
- System tracks record-to-dataset-to-shard-to-slice lineage.
- System identifies all affected shards.
- System resumes from checkpoint immediately before earliest affected slice.
- System retrains that slice and later slices in affected shard(s).
- System leaves unaffected shards unchanged.
- System supports clean full-retraining reference for research.
- System records all training configuration and environment metadata.

### FR-08 Verification evidence
- Each deletion request has a policy-defined evidence checklist.
- Evidence records result, timestamp, verifier version and opaque reference.
- Missing or failed mandatory evidence blocks completion.
- Backup handling is explicitly reported.
- Model-level tests are described as empirical evidence, not proof of zero residual information.

### FR-09 Certificate
- Generate certificate only after completion policy passes.
- Certificate contains no PII or conversation content.
- Certificate payload is canonicalized and signed with Ed25519.
- Public key is discoverable by key ID.
- QR code encodes HTTPS verification URL.
- Certificate can be revoked/superseded with reason category and audit entry.
- Verification detects unknown IDs, altered payloads, invalid signatures and revoked certificates.

### FR-10 Public verifier
- Anyone can scan QR or enter certificate ID.
- Public page displays authenticity and policy outcome separately.
- Public page must not reveal identity, conversation text, raw data hashes or internal storage paths.
- If verification service is unavailable, show unavailable—not valid.

## 5. Non-functional requirements

### Performance
- Chat response latency is measured and reported.
- Consent withdrawal/tombstone latency is measured.
- Deletion job duration is reported.
- Public verification target: p95 under 2 seconds on local test deployment (target, not guarantee).

### Reliability
- Jobs are idempotent.
- Worker crash recovery is supported.
- State transitions are transactional.
- Model promotion is atomic with rollback.
- A stale worker cannot publish an outdated model.

### Security
- TLS in deployment.
- Least-privilege service accounts.
- Secrets not stored in Git.
- Rate limiting on authentication, deletion and verification endpoints.
- Input validation and output encoding.
- Audit log protected from ordinary application mutation.
- Backups encrypted and retention documented.

### Privacy
- Minimize data collection.
- Pseudonymous training record IDs.
- Keep identity mapping separately protected.
- No training without explicit consent.
- No PII in public certificates.
- Retention and backup deletion semantics disclosed.

### Accessibility
- Keyboard navigation.
- Visible focus indicators.
- Screen-reader labels.
- Color is not the only status indicator.
- Plain-language privacy explanations.

## 6. Main screens

1. Login/register.
2. Chat.
3. Privacy settings.
4. Data inventory.
5. Delete data confirmation.
6. Deletion progress.
7. Certificate detail.
8. Public verification.
9. Research/admin dashboard (restricted).

## 7. Deletion UX copy

### Before request
“Your request will stop future use of the selected data immediately. If the data was already used to train a model, the system will run the configured unlearning process. This can take time. A certificate is issued only after the required checks complete.”

### Acknowledgement
“Your request has been received. The data has been placed under an exclusion hold. This does not yet mean model unlearning is complete.”

### Completed
“The deletion workflow completed under policy version X. The certificate verifies the platform's signed record and the checks listed in it. It is not a mathematical proof that no model can reproduce any information.”

### Failed/partial
“Some required checks did not complete. Your data remains excluded from future training. The request is not certified as completed. See the status details.”

## 8. Success metrics

Product metrics:
- Consent preference changes correctly enforced.
- Percentage of deletion requests with complete lineage.
- Tombstone latency.
- Deletion workflow completion/failure rate.
- Certificate verification success and latency.
- Number of stale jobs blocked.
- Privacy incidents (target zero).

Research metrics are defined in `08_RESEARCH_METRICS_AND_RESULT_FORMAT.md`.

## 9. MVP release gates

Do not release even as a controlled demo until:
- Consent default and enforcement tests pass.
- Deletion request is idempotent.
- Tombstone blocks training inclusion.
- Stale job commit is blocked.
- Certificate cannot show completed with failed evidence.
- Signature tampering tests pass.
- Public verifier leaks no PII.
- Resource safety limits are tested.
- Known limitations are shown to users.


## 10. Research contribution requirements

### RC-FR-01 Merkle transparency log
- Every certificate issuance/revocation/supersession event is appended to an append-only Merkle log.
- Public verifier can request inclusion proof and signed tree head.
- Verifier can check consistency between a previously observed tree head and the latest tree head.
- Public page shows transparency-log verification separately from certificate signature and deletion evidence.
- No PII or raw user data is included in log leaves.

### RC-FR-02 Training-job race prevention
- Every training job is bound to an exclusion epoch and dataset manifest digest.
- Deletion request increments epoch atomically with tombstone creation.
- Worker must validate epoch before reading, at slice boundaries and before artifact publication.
- Stale workers cannot publish checkpoints or deploy models.
- User dashboard reports immediate exclusion separately from unlearning completion.

### RC-FR-03 Cost-aware SISA configuration
- Admin/research dashboard supports experiment configurations for shard and slice counts.
- Metrics include initial training time, deletion retraining time, checkpoint storage, utility, forgetting and inference latency.
- Deletion position and affected shard fraction are recorded.
- System can export a comparison table and Pareto-frontier data.
- Configuration recommendations must respect the device resource profile and not claim a universally optimal configuration.

## 11. Additional product acceptance criteria

- Merkle inclusion proof validates for every completed certificate.
- Modified leaf, invalid tree-head signature or invalid proof is rejected.
- Consistency proof detects an inconsistent tree history in controlled tests.
- A worker with stale exclusion epoch is unable to publish an artifact.
- Race tests cover active training and checkpoint/model publication windows.
- SISA configuration experiment records all six cost/quality dimensions.
- UI distinguishes certificate signature validity, Merkle-log inclusion and deletion evidence status.
