# CryptoForget: Verifiable Machine Unlearning with SISA Sharding, Epoch-Fenced Pre-Tombstoning, and Merkle Deletion Certificates

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.6.0-EE4C2C.svg)](https://pytorch.org)
[![React](https://img.shields.io/badge/React-19.0-61DAFB.svg)](https://react.dev)
[![AWS S3](https://img.shields.io/badge/AWS%20S3-Artifacts%20Synced-FF9900.svg)](https://aws.amazon.com/s3/)
[![Tests](https://img.shields.io/badge/Tests-28%20Passed-brightgreen.svg)]()

**CryptoForget** is an end-to-end privacy-preserving conversational AI platform that unites exact Sharded, Isolated, Sliced, and Aggregated (**SISA**) machine unlearning with cryptographic proof of deletion compliance. Designed to fulfill the ``Right to be Forgotten'' (GDPR Article 17) without computationally prohibitive full-model retraining, CryptoForget enables verifiable data deletion with empirical speedups up to **6.62$\times$** and zero PII disclosure.

---

## 🌟 Core Research Contributions

### 1. RC1 — Append-Only Merkle Deletion Transparency Log
- Maintains an RFC 6962--compliant Merkle tree tracking all certificate issuance, revocation, and supersession events.
- Employs prefix domain separation (`0x00` leaf, `0x01` internal nodes) and generates Signed Tree Heads (STH) with Ed25519 digital signatures.
- Enables independent verifiers to check $O(\log N)$ inclusion proofs and historical consistency proofs without disclosing personal data.
- **Empirical Performance:** Sub-millisecond append latency ($p_{95} = 0.606$ ms), sub-millisecond inclusion proof verification ($0.119$ ms), and **100% tamper detection**.

### 2. RC2 — Concurrency Fencing & Deletion-Race Barrier
- Eliminates race conditions where a training worker concurrently commits model checkpoints containing tombstoned records.
- Enforces an atomic exclusion barrier: deletion acceptance commits tombstones and increments the global dataset $\text{ExclusionEpoch}$ in a single transaction.
- Training workers are issued lease-bound fencing tokens; stale epochs or expired leases trigger an immediate `StaleJobFencingError`.
- **Empirical Safety:** **0 post-request stale commits** across all empirical trials (100% stale commit rejection rate).

### 3. RC3 — Cost-Aware SISA Configuration Selector
- Systematically models initial training compute, selective retraining latency, checkpoint storage footprint, and logit-ensemble inference overhead.
- Identifies the non-dominated **Pareto frontier** across multi-objective dimensions ($K \in \{2, 4\}$ shards, $S \in \{2, 3, 5\}$ slices).
- Computes empirical break-even request counts ($N_{\text{break\_even}} = T_{\text{init}} / (T_{\text{full}} - T_{\text{sisa}})$) and provides an automated configuration recommender based on expected deletion workloads.

---

## 📊 Empirical Results Summary

Evaluated on **DistilGPT2 (81.9M parameters)** fine-tuned on conversational sequences under strict CPU hardware constraints (Intel Core i5 12th Gen, batch size 1, sequence length 128):

### Table A: Main Efficiency Results
| Method | Shards ($K$) | Slices ($S$) | Initial Train (min) | Deletion Train (min) | End-to-End Deletion (min) | Speedup | Time Saved (\%) | Break-Even ($N$) |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **M1 Clean Full Retrain** | --- | --- | --- | 0.155 | 0.155 | 1.00$\times$ | 0.0\% | --- |
| **SISA $2\times2$** | 2 | 2 | 0.225 | 0.023 | 0.023 | **6.62$\times$** | **84.89\%** | **1.7** |
| **SISA $2\times3$** | 2 | 3 | 0.445 | 0.040 | 0.040 | 3.89$\times$ | 74.28\% | 3.9 |
| **SISA $4\times2$** | 4 | 2 | 0.445 | 0.034 | 0.034 | 4.49$\times$ | 77.72\% | 3.7 |
| **SISA $4\times3$** | 4 | 3 | 0.687 | 0.039 | 0.039 | 3.94$\times$ | 74.59\% | 5.9 |
| **SISA $2\times5$** | 2 | 5 | 0.614 | 0.082 | 0.082 | 1.89$\times$ | 47.09\% | 8.4 |

### Table C: Utility, Privacy & Forgetting Ablations ($K=2, S=3$)
| Method | Validation Loss | Perplexity | MIA AUC | MIA Advantage | Mean KL to Clean ($M1$) |
|:---|:---:|:---:|:---:|:---:|:---:|
| **M0 Original** | 0.8153 | 2.26 | 0.472 | 0.000 | 1.9110 |
| **M1 Clean Full Retrain** | 0.5219 | 1.69 | 0.000 | 0.000 | **0.0000** |
| **M2 SISA Unlearned** | 1.9316 | 6.90 | 0.667 | 0.083 | 4.0284 |
| **M3 SISA w/o Fencing** | 0.8153 | 2.26 | 0.472 | 0.000 | 1.9110 |
| **M4 Tombstone Only** | 0.8153 | 2.26 | 0.472 | 0.000 | 1.9110 |

---

## 🏛️ System Architecture

```mermaid
flowchart TD
    User([User / Web Client]) -->|Chat / Consent / Deletion| API[FastAPI Gateway]
    
    subgraph Control_Plane [Control & Lineage Plane]
        API --> DB[(SQLite Database)]
        DB --> Consent[Consent Manager (Default OFF)]
        DB --> Lineage[Lineage Store (Shards/Slices)]
        DB --> Tombstone[Pre-Tombstoning Barrier]
        Tombstone --> Epoch[Exclusion Epoch Manager]
    end

    subgraph ML_Plane [Machine Unlearning Plane]
        Epoch -->|Epoch & Leases| Fencing[Commit-Time Fencing Gate (RC2)]
        Fencing --> SISATrainer[SISA Trainer / Unlearner]
        SISATrainer --> Checkpoints[(Slice Checkpoints Base/Suffix)]
        Checkpoints --> Ensemble[Logit Distribution Aggregator]
        Ensemble --> ModelRegistry[Model Registry & Atomic Promotion]
    end

    subgraph Crypto_Plane [Transparency & Certification Plane]
        ModelRegistry --> Orchestrator[Deletion Orchestrator (5-Point Matrix)]
        Orchestrator --> Manifest[RFC 8785 Evidence Manifest]
        Manifest --> Signer[Ed25519 Certificate Signer]
        Signer --> Merkle[RFC 6962 Append-Only Merkle Log (RC1)]
        Merkle --> S3[(AWS S3 Artifact Store)]
        Signer --> PublicVerifier[Public Zero-PII Verifier (/verify/:id)]
    end

    PublicVerifier -->|Authentic Verification| Auditor([Independent Auditor])
```

---

## 🚀 Quickstart & One-Click Reproduction

### Prerequisites
- Python 3.12+ in a virtual environment (`.venv`)
- Node.js 20+ & npm (for frontend)
- AWS CLI configured with profile `cryptoforget` (or local mock for offline testing)

### Installation
```bash
# 1. Clone repository and navigate to root
cd "Revamp CryptoForget"

# 2. Activate virtual environment
.\.venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
cd frontend && npm install && cd ..
```

### One-Click Reproduction Pipeline
To reproduce all experiments, run the automated master harness:
```bash
$env:PYTHONPATH="backend;."
python scripts/reproduce_all.py
```
This single command executes:
1. Pinned model verification (`models/distilgpt2`)
2. Database schema initialization (`data/cryptoforget.db`)
3. Full unit and integration test suite (**28/28 tests passed**)
4. Baseline benchmark execution ($M0$ and $M1$)
5. SISA grid sweep ($K \in \{2, 4\}, S \in \{2, 3, 5\}$) and ablations ($M0 \dots M4$)
6. Results analysis, Pareto frontier calculation, and table generation
7. AWS S3 synchronization to `s3://cryptoforget-artifacts-313696198691/experiments/phase8/`
8. Generates `data/results/REPRODUCIBILITY_VERIFICATION.md`

### Running the Interactive Web Application
```bash
# Terminal 1: Launch Backend API (FastAPI)
$env:PYTHONPATH="backend;."
uvicorn app.main:app --port 8000 --host 127.0.0.1 --reload

# Terminal 2: Launch Frontend UI (React + Vite)
cd frontend
npm run dev -- --port 5173 --host 127.0.0.1
```
Open [http://127.0.0.1:5173](http://127.0.0.1:5173) in your browser.

---

## 🔒 Claims Boundaries & Ethics Notice

In compliance with Doc 01 (§1) and Doc 08 (§16):
- **Cryptographic vs. Mathematical Claims:** CryptoForget certificates verify that a named platform policy was executed through audited checkpoints (source redaction, cache invalidation, affected suffix retraining, and transparency logging). **They do not constitute a mathematical proof of zero residual Shannon/Bayesian information in neural weights.**
- **Zero PII in Transparency Logs:** Transparency leaves commit exclusively to opaque identifiers, event types, timestamps, and SHA-256 digests. No user messages, names, emails, or unhashed identifiers are ever written to the Merkle log or public verifier.
- **Dedicated Cloud Credentials:** All S3 interactions explicitly require `profile_name="cryptoforget"` in `ap-south-1` to prevent modifying host credentials.

---

## 📁 Repository Structure

```
Revamp CryptoForget/
├── backend/app/                 # FastAPI Backend
│   ├── api/v1/                  # REST API routes (chat, consent, deletion, certificates, transparency)
│   ├── crypto/                  # RFC 8785 JCS, Ed25519 signer, RFC 6962 Merkle log
│   ├── db/                      # SQLAlchemy models & SQLite session factory
│   ├── models/                  # Domain entity schemas
│   ├── services/                # Deletion orchestrator, Certificate service, S3 client
│   └── worker/                  # Concurrency fencing & Exclusion epoch manager (RC2)
├── frontend/src/                # React 19 + TypeScript + Tailwind UI
│   ├── components/              # Chat, Consent modal, Deletion stepper, Public verifier
│   └── App.tsx                  # Client routing and layout
├── ml/                          # PyTorch SISA Engine & Metrics
│   ├── data/                    # DatasetBuilder, SISAPartitioner, Exclusion manifests
│   ├── evaluation/              # Efficiency, Utility, Forgetting (MIA, KL) metrics
│   ├── inference/               # SISAEnsemble logit distribution aggregator
│   ├── registry/                # ModelRegistry with atomic rollback
│   ├── scripts/                 # Grid experiments, baseline benchmarks, results analyzer
│   └── training/                # SISATrainer, BaselineTrainer, ResourceMonitor
├── paper/                       # Research Paper (LaTeX Package)
│   ├── main.tex                 # Publication-ready IEEE/ACM manuscript
│   ├── references.bib           # Bibliography
│   └── tables/                  # Empirical Tables A, B, C, D and Pareto frontier
├── scripts/                     # Reproducibility automation
│   └── reproduce_all.py         # One-click reproduction script
├── tests/                       # Automated Test Suite (28 tests)
│   ├── integration/             # Deletion flow, Concurrency race, Public verification
│   └── unit/                    # SISA, Fencing, Merkle, Certificates, Consent
├── docs/                        # Specifications and design guidelines (Phases 0-9)
└── README.md                    # Project documentation
```

---

## 📄 Citation

```bibtex
@article{cryptoforget2026,
  title={CryptoForget: Verifiable Machine Unlearning with SISA Sharding, Epoch-Fenced Pre-Tombstoning, and Merkle Deletion Certificates},
  author={Student Research Group},
  institution={Vishwakarma Institute of Technology, Pune},
  year={2026}
}
```
