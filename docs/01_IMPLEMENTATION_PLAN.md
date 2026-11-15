# Implementation Plan: Privacy-Preserving Conversational AI with SISA Unlearning and Verifiable Deletion

**Document status:** Research implementation blueprint  
**Version:** 1.0  
**Date:** 2026-11-02  
**Primary hardware target:** 16 GB RAM, Intel Core i5 12th generation, Intel Iris Xe, Windows + WSL2  
**Research model candidate:** SmolLM2-360M (subject to model-card/license review and reproducibility lock)

## 1. Executive summary

Build a privacy-first conversational AI system with:
1. A ChatGPT-like web interface.
2. Explicit, versioned consent for use of conversations in model training.
3. Data lineage from user records to dataset versions, SISA shards, slices, checkpoints and deployed model versions.
4. Pre-tombstoning: immediate exclusion of records from future processing after an authorized deletion request.
5. Source/derived-data deletion under a documented retention and backup policy.
6. SISA-based selective retraining for data already used in training.
7. An evidence-driven deletion verification workflow.
8. Ed25519-signed certificates, SHA-256 digests, QR codes and a public verification page.
9. A reproducible research harness comparing full retraining with SISA and ablations.

**Critical claim boundary:** A valid digital signature proves that the certificate was signed by the holder of a signing key and was not altered. It does not, by itself, prove that data was deleted or that a neural network has zero residual information. The platform must describe the certificate as cryptographically authentic evidence of specified checks performed under a named policy—not as mathematical proof of perfect erasure.

## 2. Research questions and hypotheses

### RQ1 — Efficiency
How much can SISA reduce deletion-triggered retraining compute/time compared with full retraining, under controlled data, initialization and training settings?

- H1: For requests affecting a subset of shards and early-to-middle slices, SISA reduces deletion-triggered training steps and wall-clock time compared with full retraining.
- Boundary: Initial SISA training and storage costs must also be reported. Do not report only deletion-time savings.

### RQ2 — Utility and forgetting
How closely does the SISA-unlearned model match a clean model trained from the same initial checkpoint without the deleted records?

- H2: SISA can preserve task utility while reducing target-record memorization/membership signal, with differences depending on shard/slice configuration.

### RQ3 — Pre-tombstoning
Can the platform prevent a deletion-requested record from entering any subsequently started or committed training job before model retraining completes?

- H3: A transactionally enforced tombstone/exclusion manifest can provide a measurable request-to-exclusion latency independent of retraining duration.

### RQ4 — Verifiable evidence
Can a third party verify certificate authenticity, integrity, status and evidence-policy outcome without seeing private user content?

- H4: Canonicalized manifests, Ed25519 signatures, public-key discovery and a transparency log support tamper-evident verification while minimizing disclosure.

### RQ5 — System overhead
What are the latency, memory, storage, inference and operational costs of the combined architecture?

## 3. Scope and non-goals

### In scope
- Single-tenant or small research deployment.
- Text-only chat.
- Explicit opt-in training consent; default off.
- User-initiated consent withdrawal and deletion.
- Full-parameter fine-tuning in controlled experiments.
- SISA with configurable shards/slices.
- Dataset lineage and exclusion manifests.
- Signed certificate and public verification.
- Local WSL2 development and safe CPU experiments.

### Out of scope for first prototype
- Production multi-region service.
- Formal proof that a neural network contains no information about a record.
- Guaranteed deletion from immutable backups before their scheduled expiry unless backup design supports targeted deletion.
- Medical/legal/financial advice product claims.
- Multi-modal training, vector database/RAG or external model-provider retention.
- Blockchain. A permissioned append-only transparency log is simpler and cheaper for the first study.

## 4. User journeys

### Journey A — Normal chat, training consent off
1. User creates account and signs in.
2. Training consent is visibly off by default.
3. User chats with the deployed model.
4. Messages may be retained only according to the separately disclosed service-retention policy.
5. Messages are not eligible for training, fine-tuning, evaluation datasets or human review for model improvement unless separately consented.

### Journey B — Opt-in and later withdrawal
1. User explicitly opts in to a clearly described training purpose.
2. System stores a consent event with policy version, timestamp, purpose and scope.
3. Only eligible records collected after the consent event enter a versioned training dataset.
4. User withdraws consent.
5. Future collection/use stops immediately.
6. User may separately request deletion of prior records and model unlearning.
7. If prior records were never used in a model, do not run SISA unnecessarily.
8. If prior records influenced a model, execute the deletion/unlearning workflow.

### Journey C — Deletion after training
1. Authenticate and authorize request.
2. Create idempotent deletion request.
3. Pre-tombstone all linked records and block new use.
4. Snapshot a signed/hashed deletion scope manifest.
5. Find raw records, dataset copies, caches, exports, derived records and model lineage.
6. Delete eligible source/derived records under policy.
7. Identify every affected shard and earliest affected slice.
8. Retrain affected shard slices from the correct checkpoint and deterministic training state.
9. validate new model, switch deployment atomically, retire old affected model.
10. Run evidence checks and model-level evaluation.
11. Issue certificate only when required policy checks pass.
12. Publish status and QR link.

## 5. Work packages and milestones

| Phase | Work | Exit criteria |
|---|---|---|
| P0 Research protocol | RQs, threat model, dataset/model selection, preregistered metrics | Protocol frozen and versioned |
| P1 Chat MVP | React UI, FastAPI, auth, inference | End-to-end chat works |
| P2 Consent/data lineage | Consent events, record IDs, training eligibility | No non-consented record enters training |
| P3 Baseline training | Full fine-tuning and clean-retrain harness | Reproducible baseline |
| P4 SISA engine | Sharding, slicing, checkpoints, selective retraining | Correct affected-shard retraining |
| P5 Pre-tombstone | Transactional exclusion and job fencing | No post-request job can commit tombstoned data |
| P6 Deletion orchestration | Raw/derived data, backup and model lineage | Deletion scope reconciled |
| P7 Evidence/certificates | Manifest, Ed25519, QR, public verifier | Tamper tests pass |
| P8 Evaluation | Efficiency, utility, forgetting, security, ablations | Results reproducible |
| P9 Paper | Methods, results, limitations, artifacts | Paper and reproducibility bundle complete |

Suggested 10–14 week student schedule:
- Weeks 1–2: protocol, literature, dataset, environment.
- Weeks 3–4: chatbot, consent and data lineage.
- Weeks 5–7: baseline full fine-tuning and SISA.
- Weeks 8–9: tombstoning, deletion orchestration and failure recovery.
- Weeks 10–11: cryptographic certificates and verifier.
- Weeks 12–14: controlled experiments, analysis, paper.

## 6. System components

### Frontend
- Chat screen with streaming responses.
- Consent settings and explanation.
- Data inventory and deletion request.
- Deletion job timeline.
- Certificate download/QR.
- Public certificate verification route.

### Backend API
- Authentication/session.
- Chat orchestration.
- Consent event service.
- Data lineage service.
- Deletion request API.
- Job status API.
- Certificate and verification APIs.

### ML service
- Model registry.
- Inference process.
- Dataset builder.
- Baseline full trainer.
- SISA trainer/unlearner.
- Evaluation runner.
- Model promotion/rollback.

### Worker
- Queue-driven jobs.
- Idempotency keys.
- Lease/heartbeat and retry policy.
- Resource admission control.
- Job fencing to prevent stale workers from publishing models.

### Storage
- PostgreSQL for transactional metadata.
- Local filesystem for development artifacts, with explicit lifecycle.
- Object storage only when deployment needs it.
- Redis only for queue/cache; never treat cache as source of truth.
- Append-only audit/transparency records.

## 7. SISA protocol

### Data partitioning
- Partition by user (or another privacy subject) to prevent a user's records being spread unpredictably across shards. If a user has records in multiple shards, support multi-shard deletion.
- Use deterministic seeded partitioning for reproducibility.
- Preserve a mapping from pseudonymous record IDs to dataset version, shard, slice and model versions in a restricted lineage store.
- Ensure test/validation data is separated and not used to tune against deletion targets.

### Training
For each shard:
1. Initialize from the same pinned pretrained checkpoint.
2. Train sequential slices.
3. Save checkpoint at slice boundaries, including model, optimizer, scheduler, RNG states, tokenizer/config, data manifest hash and code/environment revision.
4. Store training event logs and timings.
5. Keep the old deployed model immutable until replacement passes validation.

### Unlearning
For a request affecting shard s and earliest affected slice j:
1. Freeze new dataset/model jobs against the old manifest.
2. Load checkpoint before slice j.
3. Construct a new slice manifest excluding tombstoned records.
4. Retrain slice j and all later slices in that shard.
5. Repeat for every affected shard.
6. Validate model artifacts and run regression/utility tests.
7. Atomically publish a new ensemble manifest.
8. Retire old model artifacts from serving and apply artifact retention/deletion policy.

### Aggregation
For causal language models, aggregate output distributions/logits rather than averaging independently trained model weights. Use a documented aggregation method and fixed shard weights. Report inference latency and memory cost. If only one shard model is selected per request, document the routing method and its implications; do not claim it is equivalent to a full ensemble.

### Correctness baseline
For every deletion case, train a clean reference model from the same initial pretrained checkpoint and training protocol on the retained dataset. Compare SISA-unlearned model to this reference. Use multiple seeds.

## 8. Pre-tombstoning protocol

Pre-tombstoning is a control-plane exclusion barrier, not model unlearning and not physical erasure.

Required behavior:
- In one database transaction, create deletion request and tombstone/exclusion entries.
- Increment a dataset/consent epoch or exclusion-manifest version.
- All training jobs must validate their manifest epoch before reading data and again before committing artifacts.
- A job using an obsolete epoch must abort or restart.
- New dataset exports and retrieval paths must exclude tombstoned records.
- Tombstone status remains until deletion evidence is reconciled.
- A failed unlearning job does not undo tombstoning.

Measure request-to-exclusion latency. It should be independent of the retraining duration.

## 9. Deletion state machine

Recommended states:
`REQUESTED → AUTHORIZED → TOMBSTONED → SOURCE_DELETION → UNLEARNING_QUEUED → UNLEARNING_RUNNING → VERIFYING → COMPLETED`

Failure states:
`REJECTED`, `FAILED_RETRYABLE`, `FAILED_MANUAL_REVIEW`, `PARTIALLY_COMPLETED`, `REVOKED`.

Do not mark complete if:
- Any in-scope store has not been checked.
- Affected shard retraining has not completed.
- Old affected model is still serving.
- Evidence is missing or stale.
- Backup handling is unresolved under the published policy.

Expose only safe status details to the public verifier.

## 10. Certificate protocol

### Signed payload
Use a versioned schema containing:
- certificate ID (random, non-identifying)
- request ID (opaque)
- issued timestamp
- completion timestamp
- schema/policy version
- model/dataset scope identifiers (non-sensitive versions)
- tombstoning result
- source/derived store check results
- affected shard count (avoid revealing private content)
- unlearning job reference
- old-model retirement status
- backup policy status
- evidence manifest digest
- signing key ID
- signature algorithm
- certificate status/revocation pointer

### Signing
- Canonicalize JSON using RFC 8785 or a rigorously specified deterministic encoding.
- Compute SHA-256 over canonical payload/evidence manifest.
- Sign canonical payload (or a well-defined envelope) using Ed25519.
- Publish public key and key ID; keep private key outside source code and ordinary database.
- Use KMS/HSM or OS-protected secret store in production.
- Retain historical public keys for verification after rotation.
- Log certificate issuance/revocation in append-only transparency log.

### QR
QR contains only an HTTPS verification URL:
`https://<domain>/verify/<opaque-certificate-id>`
Never place PII, message content, hashes of low-entropy personal data, or signing secrets in QR.

### Public result states
- `VALID_COMPLETED`: recognized certificate, signature valid, not revoked, all policy checks pass.
- `VALID_PENDING`: authentic request but workflow incomplete.
- `INVALID`: unknown ID, bad signature, altered payload, revoked certificate or failed required policy.
- `UNAVAILABLE`: verifier cannot reach source of truth; do not silently display valid.

## 11. API outline

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/v1/chat` | Send message |
| GET | `/api/v1/consent` | Read current consent |
| PUT | `/api/v1/consent` | Change consent |
| GET | `/api/v1/data-inventory` | Show retained data categories |
| POST | `/api/v1/deletion-requests` | Request deletion |
| GET | `/api/v1/deletion-requests/{id}` | Job status |
| GET | `/api/v1/certificates/{id}` | Owner certificate |
| GET | `/verify/{certificate_id}` | Public verification page |
| GET | `/.well-known/verification-keys.json` | Public signing keys |
| GET | `/api/v1/transparency/{id}` | Public audit inclusion proof |

Use authentication and authorization on all private routes. Public verification must disclose no user identity or chat content.

## 12. Acceptance criteria

- Training consent defaults to off.
- A record without valid consent cannot enter a training manifest.
- Consent withdrawal blocks future inclusion.
- Deletion request is idempotent.
- Tombstones are committed before unlearning starts.
- Stale training jobs cannot publish artifacts.
- All affected shards are retrained from correct checkpoints.
- Unaffected shards are not retrained.
- Full-retrain reference is generated for evaluation.
- Old affected model is not served after successful model promotion.
- Every certificate signature verifies.
- Any payload alteration causes verification failure.
- Incomplete workflow cannot produce `VALID_COMPLETED`.
- Public verifier does not expose personal information.
- Resource limits prevent unsafe training jobs on the target laptop.

## 13. Research deliverables

1. Working chatbot.
2. Consent and data lineage subsystem.
3. SISA trainer/unlearner.
4. Pre-tombstoning gate.
5. Deletion orchestration and evidence manifest.
6. Certificate signer and QR verifier.
7. Reproducible experiment scripts/configs.
8. Raw anonymized metric tables and analysis notebooks.
9. Threat model and privacy assessment.
10. Research paper and limitations statement.


## 14. Cross-cutting research contributions (mandatory architecture)

The following three contributions are first-class system requirements, not optional future ideas.

### RC1 — Merkle-based deletion transparency log
- Every certificate issuance, revocation and supersession event is appended to a Merkle transparency log.
- Leaf entries commit to certificate ID, event type, event timestamp, certificate payload digest and evidence-manifest digest; never include PII or raw record identifiers.
- Publish signed tree roots with monotonically increasing tree size and timestamp.
- Provide inclusion proofs and consistency proofs to independent verifiers.
- Verifier checks signature, inclusion, consistency against a previously observed root, certificate status and evidence-policy result.
- Research measures: append latency, proof generation/verification latency, proof size, log throughput, tamper detection and consistency-fork detection in simulated tests.
- A Merkle log proves inclusion/consistency relative to published roots; it does not prove that the underlying deletion actually occurred.

### RC2 — Training-job race prevention
- Introduce a monotonically increasing exclusion epoch per dataset scope.
- Every training job records the epoch and immutable dataset manifest digest it started with.
- Workers validate epoch before reading records, at slice start, and immediately before publishing a checkpoint/model.
- A deletion transaction commits tombstones and increments the epoch atomically.
- A worker whose epoch is stale must not publish; it aborts or restarts from a fresh exclusion manifest.
- Use fencing tokens/leases so a timed-out or partitioned worker cannot later commit stale artifacts.
- Test races at dataset construction, data loading, forward/backward pass, checkpoint write and model promotion.
- Research measures: stale-job rejection rate, post-request inclusion count, tombstone latency, abort/restart cost and false abort rate.

### RC3 — Cost-aware SISA configuration
- Treat shard count and slice count as tunable design variables.
- Evaluate initial training cost, deletion retraining time, checkpoint storage, model utility, forgetting metrics and inference latency together.
- Include deletion position (early/middle/late), affected shard fraction and deletion size in the experiment design.
- Derive empirical break-even deletion request count, including initial SISA training cost.
- Develop a configuration selector that recommends a Pareto-efficient shard/slice setting for a specified deletion workload and resource budget.
- Do not optimize retraining time alone; report utility, privacy and serving trade-offs.

These contributions must appear in the PRD, engineering rules, stack, privacy model, device guardrails, design rules and paper metrics. Each must have acceptance tests.
