# Engineering Rules and Agent Operating Rules

**Version:** 1.0  
**Date:** 2026-11-02

These rules apply to developers and any AI coding agent operating in this repository.

## 1. Non-negotiable rules

1. Never train on user data without explicit, current, purpose-specific consent.
2. Consent defaults to off.
3. Never interpret consent withdrawal as proof that previously learned model influence is removed.
4. Never claim tombstoning equals physical deletion or model unlearning.
5. Never issue a completed deletion certificate unless every mandatory policy check passes.
6. Never claim a signature proves the underlying deletion event happened.
7. Never expose PII, chat content, raw user IDs or internal storage locations in public verification.
8. Never commit secrets, private keys, credentials, tokens or real user datasets.
9. Never run unrestricted training jobs on the user's host OS.
10. Never delete checkpoints/backups before lineage and retention policy checks.
11. Never overwrite the only known-good model.
12. Never silently change experiment configuration or model revision.

## 2. Repository rules

- Keep frontend, backend, ML engine, worker and certificate code separated.
- Use typed request/response schemas.
- Use database migrations; do not mutate production schema manually.
- Pin dependencies and model revisions for reproducibility.
- Every experiment must have a config file and run ID.
- Every model artifact must include model ID, code commit, dataset manifest digest, seed and config.
- Keep generated datasets and checkpoints out of Git.
- Use `.env.example`, never `.env` in Git.
- Keep test fixtures synthetic.

## 3. Coding rules

- Python: type hints for public functions; small modules; explicit exceptions.
- API: validate every request; enforce authentication and authorization.
- Database: parameterized queries/ORM; transactions for state changes.
- Worker: idempotent tasks; bounded retries; timeouts; heartbeats.
- ML: deterministic seed controls; checkpoint all needed state; no hidden global configuration.
- Cryptography: use vetted library primitives; no custom algorithms.
- Frontend: no secrets in browser; no PII in analytics or console logs.
- Logging: structured, redacted, retention-limited.

## 4. State and concurrency rules

- Deletion request creation and tombstone insertion must be atomic.
- Training jobs must capture an exclusion-manifest version.
- Before publishing any dataset/model artifact, worker rechecks that version.
- If version changed, abort/rebuild.
- Use optimistic locking or explicit job fencing tokens.
- Model deployment uses immutable version directories and atomic pointer/manifest switch.
- A failed job must not revert tombstones.
- Duplicate deletion requests return the existing request or a safe idempotent result.

## 5. ML experiment rules

- Use the same initial checkpoint for clean retraining and SISA comparisons.
- Use same retained training records, tokenization, optimizer, scheduler, sequence length and compute budget where applicable.
- Record at least 3 seeds for final paper if compute allows; clearly label fewer seeds as a limitation.
- Split by privacy subject where feasible.
- Prevent train/test contamination.
- Keep deletion targets out of validation/test data unless a separate attack/evaluation design requires them.
- Report initial SISA training cost, unlearning cost, storage and inference overhead.
- Do not compare one SISA seed against a multi-seed full retraining mean.
- Do not tune hyperparameters on the test set.
- Save optimizer, scheduler and RNG states at slice boundaries.
- Distinguish exact replay from approximate retraining.

## 6. Certificate rules

- Canonical serialization must be specified and tested.
- Sign only after evidence policy passes.
- Store signed payload, signature, key ID and schema version.
- Verify signature before displaying payload as authentic.
- Check revocation and status separately from signature validity.
- Preserve public keys for historical verification.
- Do not publish unsalted hashes of low-entropy private data.
- Certificate IDs must be random and unguessable.
- QR code only contains the public HTTPS verification URL.
- If verifier cannot reach authoritative status store, return unavailable.

## 7. Testing rules

Required automated tests:
- Consent-off data exclusion.
- Consent withdrawal race with dataset build.
- Tombstone race with active worker.
- Multi-shard user deletion.
- Correct checkpoint selection.
- Slice replay determinism.
- Model promotion/rollback.
- Backup restore does not resurrect tombstoned records.
- Signature valid/invalid.
- Payload tampering.
- Key rotation.
- Revoked certificate.
- Public endpoint privacy.
- Resource guardrail enforcement.

## 8. Pull request checklist

- [ ] Tests added and passing.
- [ ] No secrets or PII.
- [ ] Migrations included if needed.
- [ ] Logs are redacted.
- [ ] Consent/tombstone logic considered.
- [ ] Failure/retry behavior documented.
- [ ] Research configuration and metrics updated.
- [ ] Resource limits respected.
- [ ] Claims in UI/docs match actual evidence.


## 9. Mandatory rules for the three research contributions

### Merkle transparency log
- Use a documented Merkle tree construction and leaf/node domain separation.
- Use deterministic leaf serialization and SHA-256 (or a separately justified hash).
- Sign tree heads with a dedicated key, distinct from certificate-signing key where practical.
- Include tree size, root hash, timestamp and key ID in signed tree head.
- Implement inclusion and consistency proof verification.
- Never mutate historical leaves; append revocation/supersession as new events.
- Keep private information out of leaves; avoid publicly guessable hashes of personal data.
- Test proof tampering, omitted entries, tree-head rollback and inconsistent roots.

### Training-job race prevention
- Dataset exclusion epoch is monotonically increasing.
- Job captures epoch + dataset manifest digest + fencing token at start.
- Validate before read, at each slice boundary and before artifact publish.
- Tombstone creation and epoch increment are one transaction.
- A stale job cannot publish even if it completes computation after losing its lease.
- Use immutable artifact paths and atomic manifest promotion.
- Do not rely only on a worker's in-memory tombstone cache.
- Test races at every stage and inject worker crashes/network delays.

### Cost-aware SISA
- Every run records shard count, slice count, deletion position, affected-shard fraction and deletion size.
- Record initial training cost and deletion-time cost separately.
- Record checkpoint storage and inference latency.
- Record model utility and forgetting metrics alongside speed.
- Use Pareto analysis; do not collapse incompatible objectives into one arbitrary score without sensitivity analysis.
- Include break-even deletion volume and hardware budget.
- Keep a baseline config and immutable experiment results.

## 10. Required tests for RC1–RC3

- Merkle inclusion proof valid/invalid cases.
- Merkle consistency proof valid/invalid cases.
- Signed tree-head signature and key-rotation tests.
- Tree rollback/fork simulation.
- Worker epoch stale before read.
- Worker epoch changes during slice.
- Worker epoch changes after training but before checkpoint publication.
- Worker lease expires and old worker attempts commit.
- Multi-shard deletion invalidates every affected worker.
- SISA shard/slice sweep captures initial cost, deletion cost, storage, utility, forgetting and inference.
