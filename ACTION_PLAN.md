# CryptoForget: Action Plan & Implementation Roadmap

This document defines the phase-by-phase action plan for building **CryptoForget: A Cryptographically Verifiable Machine Unlearning Framework for Production MLOps Systems**.

> [!IMPORTANT]
> **Leveraging Existing Codebase Model**: CryptoForget will directly use the existing, pre-trained dynamic news recommendation model (`NewsContentModel`, `DynamicRecommender`, `EventDynamicProfileBuilder`) and dataset (MIND-small dataset in `data/raw/MINDsmall_train` and pre-built artifacts in `models/content_model.joblib` & `models/user_histories.joblib`).

---

## Phase 0: System Foundations & Existing Model Integration

### Objectives
Establish the system architecture, database ORM schemas, database connection layer, and integrate the existing MIND-small recommendation model (`models/content_model.joblib` & `models/user_histories.joblib`).

### Entry Criteria
- Project Synopsis approved.
- Existing ML model (`models/content_model.joblib`, `models/user_histories.joblib`) available in current codebase.
- Python 3.11 virtual environment active.

### Detailed Tasks
- [ ] **Task 0.1**: Update `src/config.py` for global environment variables (database URIs, MLflow URI, `MODELS_DIR="models"`, SISA shard count $S=5$, ECDSA key paths).
- [ ] **Task 0.2**: Create SQLAlchemy / Pydantic ORM models in `src/db/models.py`:
  - `User`: User profile ID (e.g., MIND user IDs `U1000`, `U1001`), consent status, onboarding timestamp.
  - `UserInteractionRecord`: User click/impression history records, dataset slice ID, ingestion Merkle leaf hash.
  - `DeletionRequest`: Request tracking ID, user ID, status (`pending`, `tombstoned`, `retraining`, `completed`), Path A vs Path B flag, affected SISA shard IDs.
  - `AuditLogEntry`: Append-only hash-chained record (`block_id`, `timestamp`, `action`, `payload_hash`, `prev_hash`, `curr_hash`).
  - `DeletionCertificate`: Serialized certificate record (`certificate_id`, `user_id`, `old_root`, `new_root`, `merkle_proof`, `old_model_hash`, `new_model_hash`, `signature`).
- [ ] **Task 0.3**: Implement `src/db/database.py` database session initializer (SQLite / PostgreSQL / CockroachDB support).
- [ ] **Task 0.4**: Implement `scripts/load_existing_model_data.py` to inspect and map the existing ~49,108 MIND user histories and ~51,282 news item TF-IDF representations into the database & feature store pipeline.

### Exit Criteria
- Existing model artifacts (`content_model.joblib` and `user_histories.joblib`) successfully connected and verified via `tests/test_db.py`.
- Database schema initialized with MIND user profiles and audit log tables.

---

## Phase 1: Cryptographic Verification Layer

### Objectives
Implement SHA-256 Merkle Tree commitments over user history/interaction batches, an append-only hash-chained audit log, ECDSA digital signatures, and cryptographic exclusion proof certificates.

### Entry Criteria
- Phase 0 complete (existing model and database schemas verified).
- Cryptographic packages installed (`hashlib`, `cryptography`, `ecdsa`).

### Detailed Tasks
- [ ] **Task 1.1**: Build `src/crypto/merkle.py`:
  - Leaf hash computation from user interaction records (user_id + history news_ids).
  - Merkle Tree construction and root calculation over MIND corpus user profiles.
  - Proof of Inclusion generation (sibling hashes path).
  - Proof of Exclusion / Absence generation for deleted/unlearned user profiles.
  - Independent verification function: `verify_merkle_proof(leaf_hash, root_hash, proof) -> bool`.
- [ ] **Task 1.2**: Build `src/crypto/audit_log.py` (`AuditLedger` class):
  - Append-only hash chain linking previous block hash to current block hash.
  - Tamper detection validator: `verify_ledger_integrity() -> bool`.
- [ ] **Task 1.3**: Build `src/crypto/ecdsa_signer.py`:
  - ECDSA SECP256k1 key generation, private key signing, and public key verification routines.
- [ ] **Task 1.4**: Build `src/crypto/certificate.py`:
  - Deletion Certificate JSON generator and validator:
    - Bundles old Merkle root, new Merkle root, Merkle exclusion proof, old MLflow model hash, new MLflow model hash, timestamp, and ECDSA signature.
  - CLI/API verifier: `verify_certificate(cert_json, public_key_pem) -> bool`.
- [ ] **Task 1.5**: Create unit test suite `tests/test_crypto.py`.

### Exit Criteria
- 100% unit test pass rate on Merkle tree building, inclusion/exclusion proof verification, audit chain tampering detection, and ECDSA certificate verification.
- Certificate verification latency measured at **< 100 ms**.

---

## Phase 2: SISA Machine Unlearning Engine for Existing Model & MIA Harness

### Objectives
Implement SISA (Sharded, Isolated, Sliced, Aggregated) exact unlearning on the existing TF-IDF/Dynamic recommendation model, pre-training tombstoning, post-training shard retraining, and Membership Inference Attack (MIA) privacy evaluation.

### Entry Criteria
- Phase 0 existing model ready (`src/models/dynamic_recommender.py`, `src/models/content_representation.py`).
- Phase 1 Merkle tree commitment library functional.

### Detailed Tasks
- [ ] **Task 2.1**: Implement `src/unlearning/sisa.py` (SISA Data Manager for MIND Corpus):
  - Hash-based partitioning of the ~49,108 MIND user histories and news catalog into $S=5$ or $S=10$ independent shards.
  - Sub-slice partitioning within each shard for incremental checkpointing.
- [ ] **Task 2.2**: Implement `src/unlearning/sharded_trainer.py`:
  - Trains sharded `NewsContentModel` instances across user history shards.
  - Aggregates recommendations across active shards.
- [ ] **Task 2.3**: Implement `src/unlearning/unlearner.py` (Unlearning Pipeline):
  - **Path A (Pre-training Deletion)**: Tombstone recent live clicks in `UserClickStore` / feature store; exclude from upcoming profile updates.
  - **Path B (Post-training Deletion)**: Map target `user_id` to shard $S_k$, purge long-term user history from $S_k$, retrain shard $S_k$ TF-IDF/history representation, recompute Merkle root, and update model registry.
- [ ] **Task 2.4**: Implement `src/unlearning/scrubbing.py` (Stretch Goal): Fisher Information Matrix / profile representation scrubbing module.
- [ ] **Task 2.5**: Implement `src/unlearning/mia.py` (Membership Inference Attack Test Harness for News Recommendation):
  - Measures privacy leakage / attack accuracy of detecting whether a deleted user's history was included in the model.
- [ ] **Task 2.6**: Create unit test suites `tests/test_sisa.py` and `tests/test_mia.py`.

### Exit Criteria
- SISA shard-only retraining demonstrated to be **$\ge 3-5\times$ faster** than full model retraining.
- Post-unlearning MIA success rate on deleted user converges toward **~50%** (random guessing).
- Recommendation utility drop on remaining users is **< 2%** AUC/MRR change.

---

## Phase 3: MLOps Pipeline, Feature Store & Drift Monitoring

### Objectives
Integrate MLflow experiment tracking/registry for the sharded recommendation models, Feast feature store for user profiles, Evidently AI drift monitoring, and pipeline orchestration.

### Entry Criteria
- Phase 2 SISA unlearning engine for existing model operational.
- `mlflow`, `feast`, `evidently` packages installed.

### Detailed Tasks
- [ ] **Task 3.1**: Implement `src/mlops/registry.py`:
  - MLflow logging of recommendation model weights, shard artifacts, model hashes, and unlearning run metrics.
- [ ] **Task 3.2**: Implement `src/mlops/feature_store.py`:
  - Feature store views for user long-term and short-term profiles respecting tombstone flags.
- [ ] **Task 3.3**: Implement `src/mlops/drift.py`:
  - Evidently AI data drift calculator monitoring changes in news category distributions and user interactions pre- and post-unlearning.
- [ ] **Task 3.4**: Implement `src/mlops/orchestrator.py`:
  - Pipeline orchestrator managing automated deletion request batching and triggering shard retraining workflows.
- [ ] **Task 3.5**: Create unit test suite `tests/test_mlops.py`.

### Exit Criteria
- MLflow successfully logs and versions each sharded retraining run of the recommendation model.
- Evidently AI generates data drift reports post-unlearning.
- Automated orchestration pipeline executes end-to-end without errors.

---

## Phase 4: FastAPI REST Service & User-Agent Simulation

### Objectives
Expose complete REST API endpoints for user onboarding, live news recommendation (`POST /recommend`), click recording (`POST /clicks`), unlearning execution (`POST /delete-user`), certificate retrieval/verification, and auditor metrics.

### Entry Criteria
- Phases 1–3 modules complete and tested.

### Detailed Tasks
- [ ] **Task 4.1**: Implement `src/agents/user_simulator.py`:
  - Virtual population simulator managing 15–20 simulated user entities (from MIND dataset user pool), reading news articles, recording live clicks, and submitting unlearning requests.
- [ ] **Task 4.2**: Update `app/main.py` and API routers:
  - `app/routers/users.py`: `GET /api/v1/users`, `POST /api/v1/users/onboard`.
  - `app/routers/inference.py`: `POST /recommend` (news candidate ranking via dynamic model) and `POST /clicks` (live click ingestion).
  - `app/routers/unlearning.py`:
    - `POST /api/v1/delete-user` (triggers Path A or Path B deletion).
    - `GET /api/v1/unlearning-status/{request_id}` (polls unlearning & shard retraining status).
    - `GET /api/v1/certificate/{user_id}` (returns signed deletion certificate).
    - `POST /api/v1/verify-certificate` (validates certificate signature & Merkle exclusion proof).
  - `app/routers/auditor.py`:
    - `GET /api/v1/audit-trail` (returns hash-chained ledger blocks).
    - `GET /api/v1/drift-metrics` (returns Evidently AI drift JSON).
    - `GET /api/v1/mia-benchmark` (returns MIA privacy curves).
- [ ] **Task 4.3**: Create integration test suite `tests/test_api.py`.

### Exit Criteria
- All FastAPI endpoints return HTTP 200/201 status codes with valid schemas.
- End-to-end REST test passes: User onboarding $\rightarrow$ Recommend $\rightarrow$ Click $\rightarrow$ Delete Request $\rightarrow$ Shard Retrain $\rightarrow$ Certificate Issued $\rightarrow$ Certificate Verified.

---

## Phase 5: React Dashboard (User, Admin & Auditor Views)

### Objectives
Build an interactive frontend dashboard providing User, Admin, and Auditor portals.

### Entry Criteria
- Phase 4 FastAPI server running with accessible REST endpoints.

### Detailed Tasks
- [ ] **Task 5.1**: Initialize React + Vite application inside `frontend/`.
- [ ] **Task 5.2**: Build **User Portal View**:
  - Virtual user switcher (dropdown of simulated MIND user entities).
  - User reading history & profile panel.
  - Live news recommendation scoring widget (`POST /recommend`).
  - Prominent "Stop / Delete My Data" action button with real-time status animation.
  - Interactive Signed Certificate modal viewer with copyable/downloadable JSON.
- [ ] **Task 5.3**: Build **Admin Portal View**:
  - Model Version Registry cards (showing active MLflow versions & SISA shard status).
  - SISA Shard Retraining execution triggers & performance stats.
  - Evidently AI Drift Chart visualizations.
- [ ] **Task 5.4**: Build **Auditor Portal View**:
  - Append-only Hash-Chained Audit Ledger explorer.
  - Merkle Tree Root & Leaf hash inspector.
  - MIA Privacy benchmark chart (~50% target curve).
  - Drag-and-drop Certificate Offline Validator widget.

### Exit Criteria
- React app compiles cleanly with 0 build errors.
- Smooth user experience allowing real-time execution of data deletion, shard retraining tracking, certificate viewing, and verification.

---

## Phase 6: Benchmarking Suite & Final Verification

### Objectives
Execute final benchmarking suite, collect performance metrics against target criteria, and generate project report/walkthrough.

### Entry Criteria
- Phases 0–5 fully implemented and verified.

### Detailed Tasks
- [ ] **Task 6.1**: Implement `scripts/run_benchmarks.py` to evaluate:
  - MIA success rate on deleted users (Target: ~50%).
  - Model utility retention on remaining users (Target: < 2% AUC/MRR drop).
  - Retraining speedup ratio (Target: $\ge 3-5\times$ faster than full retrain).
  - Certificate verification latency (Target: < 100 ms).
  - Certificate size (Target: a few KB).
- [ ] **Task 6.2**: Run complete automated test suite (`pytest`) across crypto, SISA, MLOps, API, and benchmarks.
- [ ] **Task 6.3**: Write comprehensive `walkthrough.md` report summarizing implementation details, architecture diagrams, benchmark results, and instructions.

### Exit Criteria
- All target metrics in the Benchmarking Matrix met.
- Automated test suite passes with 100% green status.
- Final walkthrough artifact completed.
