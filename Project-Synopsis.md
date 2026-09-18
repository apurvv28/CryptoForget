# Vishwakarma Institute of Technology
**Issue 01 : Rev No. 00 : Dt. 01/08/22** | **FF No. 180**

## Title : Project Registration & Progress Review

| Property | Details |
| :--- | :--- |
| **Department** | CSE - AI |
| **Academic Year** | 2026-27 |
| **Semester** | I |
| **Group No.** | TY-G-01 |
| **Project Title** | **CryptoForget: A Cryptographically Verifiable Machine Unlearning Framework for Production MLOps Systems** |
| **Project Area** | Privacy and AI Ethics |

---

### Group Members Details

| Sr. No. | Class & Div. | Roll No. | G.R. No. | Name of Student | Contact No. | Email ID |
| :---: | :---: | :---: | :---: | :--- | :---: | :--- |
| 01 | TY-G | 11 | 1252090011 | Apurv Dhananjay Saktepar | 7058229202 | apurv.1252090011@vit.edu |
| 02 | TY-G | 13 | 1252090013 | Nisha Yuvraj Pragane | 9373639198 | nisha.1252090013@vit.edu |
| 03 | TY-G | 37 | 12520096 | Vedant Rajendra Bhakare | 8080210942 | vedant.bhakare25@vit.edu |
| 04 | TY-G | 51 | 1252090036 | Anushka Suresh Salvi | 9156670589 | anushka.1252090036@vit.edu |

**Name of Internal Guide:** Mrs. Prachi Ashok Pawar  
**Contact No. & Email ID:** 9503536137, prachi.pawar2@vit.edu  

---

## Abstract

The personal information of people, such as financial transactions, medical history, academic performance, and behavioral data is used to train the ML processes of today. Some laws, including the GDPR Article 17 and CCPA, dictate that if a user requests to delete their personal data, organizations must comply. However, while this means that an organization must remove the personal details from the database, the training data remain part of the model. 

The **CryptoForget** project was born out of the need for a system that demonstrates this fact and solves the problem on a small scale. The system consists of a working ML model with an MLOps pipeline (training, monitoring, review, retraining) and a virtual population of 15-20 entities, generating data through this model. Each entity has a function of cancellation of data. The system involves cryptographic commitment to the training data during its collection, generates a verifiable signed certificate of deletion after data erasure, and provides detailed reports about the performance of the model before and after erasing a user's data.

---

## Introduction

Today's ML solutions, be it a loan approval system, a diagnostic support application, or a personalized learning platform, have one thing in common: they learn based on the data provided by live users. When this data is processed, it becomes dissipated in the system and ceases to exist as an identifiable entry in a database. If the users demand that their data be erased, the company may comply with their request to delete the entry, but it could not guarantee that the impact of the data in question had disappeared as well.

The practical evidence to support this assertion has been evident in the following recent cases:
- **FTC v. Everalbum:** The FTC concluded that the company that had been using the facial recognition technology without people's consent would be obliged to eliminate the software, not only the data themselves.
- **NYT v. OpenAI, Microsoft:** The allegations that GPT-4 preserved the copyrighted texts have revived the debate about whether the language models could delete the memory of private textual data after the completion of the machine learning procedure.
- **Clearview AI (2022):** European privacy enforcers imposed penalties on Clearview AI Technologies Inc. over the use of unlawfully collected facial recognition data despite the company asserting that it had no reasonable means to verify that such data was deleted.

The reason behind these incidents is the same: AI systems do not support a native "delete" functionality and, even if approximate unlearning techniques are employed, there's no way for the user or auditor to make sure the deletion occurred and the company made its proprietary model weights public.

CryptoForget represents a practical deep research and development project whose objective is to create a working and scaled-down version of the whole pipeline necessary for solving this problem — including the domains of modern machine learning engineering, MLOps, distributed systems, applied cryptography, and privacy regulations and laws, using just one particular industry (FinTech credit risk / loan default model will be illustrated in this paper).

---

## Research Gap Analysis

| Existing Research / System | Limitation Identified | Research Gap | Proposed Solution in This Work |
| :--- | :--- | :--- | :--- |
| **Traditional ML models** | Once trained, user data remains embedded in model parameters. | No efficient mechanism to selectively remove an individual user's influence. | Implement SISA-based exact machine unlearning for selective data deletion. |
| **GDPR/CCPA compliance tools** | Deleting database records does not remove learned information from trained models. | Lack of verifiable machine learning data deletion. | Integrate machine unlearning with cryptographically verifiable deletion certificates. |
| **Existing Machine Unlearning methods** | Focus primarily on model retraining efficiency. | Limited emphasis on end-user transparency and auditability. | Generate signed deletion certificates backed by Merkle proofs and ECDSA signatures. |
| **Cryptographic verification research** | Primarily theoretical or focused on blockchain applications. | Limited integration with machine unlearning pipelines. | Combine Merkle commitments, audit logs, and machine unlearning into one framework. |
| **MLOps platforms (MLflow, Feast, etc.)** | Provide lifecycle management but lack privacy-aware retraining workflows. | No native support for right-to-be-forgotten requests. | Integrate deletion requests directly into the MLOps pipeline using FastAPI, Kafka, and Airflow/Prefect. |
| **Existing privacy-preserving ML research** | Focuses on federated learning, differential privacy, or secure inference. | Few end-to-end implementations combining MLOps, machine unlearning, and cryptographic verification. | Develop a complete end-to-end architecture integrating ML, MLOps, machine unlearning, cryptographic proofs, and user-facing dashboards. |
| **Approximate unlearning techniques** | Faster but may not guarantee complete removal of user influence. | Need practical comparison between exact and approximate unlearning. | Benchmark SISA exact retraining against Fisher-information scrubbing as a stretch goal. |
| **Academic prototypes** | Often evaluated only on algorithmic performance. | Limited focus on usability and user trust. | Provide React dashboards for users, administrators, and auditors with real-time deletion status and verification certificates. |
| **Machine learning benchmark studies** | Primarily evaluate model accuracy. | Lack of evaluation metrics for privacy and deletion effectiveness. | Evaluate MIA success rate, retraining cost, certificate generation time, deletion latency, and model utility retention. |
| **Existing literature** | Individual components are studied independently. | No unified architecture combining MLOps, cryptographic verification, machine unlearning, and regulatory compliance. | Propose a unified, modular, and deployment-ready architecture suitable for FinTech, Healthcare, and EdTech applications. |

---

## Problem Statement

How can a machine learning production system enable any user to delete their personal information, both from the ongoing education and from the model that has already received training in order to provide every user and auditor with cryptographic evidence of what has been deleted, while at the same time protecting the proprietary parameters of the model and anybody else's personal data?

It breaks down into four concrete sub-problems that the project should resolve:
1. **Deletion in a working system rather than just experimental evaluations:** A request for deletion must be implemented in a working system with users present, a live model registry, and ongoing retraining/drift cycles.
2. **Two types of deletion:**
   - **(a) Pre-training deletion:** Skipping data collection before the next retraining for data not yet used in the current model version.
   - **(b) Post-training deletion:** Real action of deletion/unlearning for data already involved in the current model.
3. **The need to verify the deletion without revealing any details:** The user should receive evidence that their data is no longer usable without needing CryptoForget to disclose details of the model and other users' data.
4. **Evidence of deletion rather than a black-box verification:** The system must provide the user and auditor with the ability to see how much influence was removed without just saying "done".

---

## Proposed Solution

CryptoForget combines three layers that are usually studied in isolation: **MLOps engineering**, **machine unlearning algorithms**, and **applied cryptography** into one demonstrable pipeline.

### 3.1 The Two Deletion Paths

- **Path A — Pre-training removal:** If user data has not yet been included in the currently deployed model version, removal involves setting respective records to tombstone in the feature store and excluding these records during the next retraining job.
- **Path B — Post-training removal:** If the current model was trained using user data, CryptoForget relies on SISA (Sharded, Isolated, Sliced, Aggregated training) to split training samples into sub-samples (shards/slices). Only the sub-sample where the deletion occurred needs to be retrained, significantly saving computational cost compared to full model retraining.

### 3.2 System Design Flow

```text
               ┌──────────────────────────────────────────────┐
               │              USER-AGENT LAYER                │
               │   15-20 simulated/real user agents           │
               │   • Onboard with synthetic personal data     │
               │   • Use live ML model (loan scoring, etc.)   │
               │   • Profile contains 'Stop/Delete My Data'   │
               └──────────────────────┬───────────────────────┘
                                      │ REST / gRPC Events
                                      ▼
               ┌──────────────────────────────────────────────┐
               │          APPLICATION + EVENT LAYER           │
               │   • FastAPI Backend                          │
               │   • Kafka Event Bus                          │
               │   • CockroachDB (User / Profile Store)       │
               └──────────┬───────────┬───────────┬───────────┘
                          │           │           │
       ┌──────────────────┘           │           └──────────────────┐
       ▼                              ▼                              ▼
┌───────────────┐             ┌───────────────┐             ┌─────────────────┐
│ MLOps PIPELINE│             │  UNLEARNING   │             │  CRYPTOGRAPHIC  │
│               │             │    ENGINE     │             │      LAYER      │
│ • Feast       │             │ • Pre-train:  │             │ • Merkle        │
│   Feature     │             │   Tombstoning │             │   Commitments   │
│   Store       │             │ • Post-train: │             │ • ECDSA Signed  │
│ • LightGBM /  │             │   SISA Shard  │             │   Deletion      │
│   Ensemble    │             │   Retraining  │             │   Certificates  │
│ • MLflow      │             │ • Fisher      │             │ • Hash-Chained  │
│   Registry    │             │   Scrubbing   │             │   Audit Log     │
│ • Evidently   │             │ • Influence   │             │ • Merkle Proof  │
│   AI Drift    │             │   Quant-      │             │   of Exclusion  │
│ • Airflow /   │             │   ification   │             └────────┬────────┘
│   Prefect     │             └───────┬───────┘                      │
└──────┬────────┘                     │                              │
       │                              │                              │
       └──────────────────────────────┼──────────────────────────────┘
                                      ▼
               ┌──────────────────────────────────────────────┐
               │               REACT DASHBOARD                │
               │   User View:                                 │
               │   • Signed deletion certificate              │
               │   • % Influence removed                      │
               │   Admin / Auditor View:                      │
               │   • Drift Charts                             │
               │   • Model Registry Versions                  │
               │   • Unlearning Audit Trail                   │
               └──────────────────────────────────────────────┘
```

### 3.3 The Cryptographic Verification Layer

1. **Commitment during ingestion:** Every batch is hashed and organized into a Merkle tree. The root hash is recorded in an append-only hash-chained audit log prior to training.
2. **Proof of inclusion (during consent):** A proof validating the presence of the user's data in the model can be provided while the model is active.
3. **Proof of exclusion (after unlearning):** When a shard is retrained/scrubbed, the new root hash is calculated. CryptoForget creates a signed deletion certificate (ECDSA signature) containing: old root, new root, Merkle proof of absence of the user's leaf, timestamp, and the hash of the new model registered in MLflow.
4. **Empirical evidence:** The dashboard presents concrete numbers before and after unlearning, such as decreasing success rate of Membership Inference Attacks (MIA) related to the deleted user's data (converging to ~50%, i.e., random guessing).

---

## Implementation Plan

| Phase | Duration | Deliverables |
| :--- | :--- | :--- |
| **0. Setup & Domain Selection** | Week 1–2 | Finalize domain (FinTech loan-default / Healthcare readmission / EdTech dropout-risk); design database schema; set up AWS project; configure CockroachDB; create repository structure. |
| **1. Core ML + MLOps Pipeline** | Week 3–6 | Develop baseline LightGBM (or sharded-ensemble) model; integrate MLflow tracking and model registry; configure Feast feature store; implement Evidently AI-based drift detection; create Airflow/Prefect retraining workflow (DAG). |
| **2. User-Agent Simulation Layer** | Week 5–7 | Develop 15–20 synthetic/real user agents using Python and Faker; build FastAPI endpoints for onboarding, model inference, and profile management; integrate Kafka event bus for user activities. |
| **3. Unlearning Engine** | Week 7–10 | Implement pre-training tombstoning; develop SISA-style sharded retraining; implement Fisher-scrubbing (stretch goal); build influence-quantification module using Membership Inference Attack (MIA) test harness. |
| **4. Cryptographic Verification Layer** | Week 9–12 | Develop Merkle tree commitment library; implement hash-chained audit ledger; build ECDSA signing service; create deletion-certificate generator and verifier (CLI/API). |
| **5. Dashboard & UX** | Week 11–13 | Develop React dashboard with user profile; implement "Stop/Delete My Data" functionality; integrate live deletion certificate viewer; build administrator/auditor dashboard with drift charts and audit trail. |
| **6. Benchmarking & Evaluation** | Week 13–15 | Execute benchmark experiments; collect evaluation metrics; perform SISA shard-count vs. retraining-cost ablation study; analyze and document results. |
| **7. Paper Writing & Submission** | Week 15–16 | Prepare IEEE/ACM-style research paper; finalize figures and experimental results; submit to conference/journal or department showcase. |

---

## Benchmarking Matrix

| Metric | Target |
| :--- | :--- |
| **Unlearning Completeness** (MIA success rate on deleted user after scrubbing) | Converges toward **~50%** (equivalent to random guessing) |
| **Model Utility Retention** (on remaining users) | **< 2%** drop in Accuracy/AUC compared to pre-deletion model |
| **Retraining Cost vs. Full Retraining** (SISA shard-only retraining) | **≥ 3–5× faster** than full model retraining |
| **Certificate Verification Time** | **< 100 ms** |
| **Certificate Size** | **A few KB** (contains only Merkle proof and ECDSA signature, not model weights) |
| **End-to-End Deletion Latency** (request to certificate issuance) | Measured, reported, and discussed rather than constrained to a fixed target |

---

## Project Feasibility

- **SISA-style Exact Unlearning:** SISA (Sharded, Isolated, Sliced, Aggregated) unlearning is a well-known methodology first described in 2021 with open-source implementations available.
- **Cryptographic Verification:** Merkle trees and ECDSA digital signatures are mature cryptographic primitives supported by standard Python libraries (`hashlib`, `cryptography`, `ecdsa`).
- **MLOps Infrastructure:** Leverages established MLOps practices (FastAPI, MLflow, Feast, Airflow/Prefect, Kafka).
- **Clearly Defined Scope:** Approximate machine unlearning via Fisher Scrubbing is designated as a stretch goal; core deliverables focus on pre-training tombstoning, SISA exact unlearning, and cryptographic deletion certificates.

---

## Technology Stack

| Layer | Technology / Framework |
| :--- | :--- |
| **ML Model** | LightGBM / XGBoost (for tabular data); optionally a small sharded neural network |
| **MLOps** | MLflow (experiment tracking & model registry), Feast (feature store), Evidently AI (drift detection), Airflow or Prefect (workflow orchestration) |
| **Backend / API** | FastAPI (Python) for REST APIs; Kafka for event streaming of user actions & deletion requests |
| **Database** | CockroachDB for user profiles, consent management, metadata, and data lineage |
| **Unlearning Engine** | Custom SISA-based sharding and retraining (LightGBM/PyTorch); Fisher Information Scrubbing (stretch goal) |
| **Cryptographic Verification** | Python `hashlib` & `cryptography` libraries for Merkle tree construction, ECDSA digital signatures, and hash-chained append-only audit log |
| **Frontend** | React-based user portal and administrator/auditor dashboard |
| **Cloud & DevOps** | AWS, Docker, and GitHub Actions for CI/CD |
| **Evaluation & Benchmarking** | Membership Inference Attack (MIA) test harness, custom benchmarking scripts |

---

## Conclusion

CryptoForget transforms the legal requirement of "the right to be forgotten" into a practical, cryptographically verifiable technical implementation. By combining an MLOps pipeline, simulated user agents, a SISA-style exact unlearning engine, and Merkle tree/ECDSA deletion certificates, CryptoForget delivers a user-verifiable confirmation of data unlearning while preserving model utility and proprietary weights.

---

## References

### 1. Foundational Machine Unlearning
1. Bourtoule, L., Chandrasekaran, V., Choquette-Choo, C. A., et al. (2021). *Machine Unlearning*. Proceedings of the IEEE Symposium on Security and Privacy. [https://arxiv.org/abs/1912.03817](https://arxiv.org/abs/1912.03817)
2. Guo, C., Goldstein, T., Hannun, A., & van der Maaten, L. (2020). *Certified Data Removal from Machine Learning Models*. Proceedings of ICML. [https://arxiv.org/abs/1911.03030](https://arxiv.org/abs/1911.03030)
3. Mercuri, S., Khraishi, R., Okhrati, R., et al. (2022). *An Introduction to Machine Unlearning*. [https://arxiv.org/abs/2209.00939](https://arxiv.org/abs/2209.00939)

### 2. Survey Papers
4. Nguyen, T. T., et al. (2022). *A Survey of Machine Unlearning*. [https://arxiv.org/abs/2209.02299](https://arxiv.org/abs/2209.02299)
5. Qu, Y., Yuan, X., Ding, M., et al. (2023). *Learn to Unlearn: A Survey on Machine Unlearning*. [https://arxiv.org/abs/2305.07512](https://arxiv.org/abs/2305.07512)
6. Shaik, T., Tao, X., Xie, H., et al. (2023). *Exploring the Landscape of Machine Unlearning: A Comprehensive Survey and Taxonomy*. [https://arxiv.org/abs/2305.06360](https://arxiv.org/abs/2305.06360)
7. Xu, H., Zhu, T., Zhang, L., et al. (2023). *Machine Unlearning: A Survey*. [https://arxiv.org/abs/2306.03558](https://arxiv.org/abs/2306.03558)
8. Wang, W., et al. (2024). *Machine Unlearning: A Comprehensive Survey*. [https://arxiv.org/abs/2405.07406](https://arxiv.org/abs/2405.07406)

### 3. Approximate and Certified Machine Unlearning
9. Golatkar, A., Achille, A., & Soatto, S. (2020). *Eternal Sunshine of the Spotless Net: Selective Forgetting in Deep Networks*. Proceedings of CVPR 2020.
10. Kurmanji, M., Triantafillou, P., Hayes, J., & Triantafillou, E. *Towards Unbounded Machine Unlearning*. [https://openreview.net/pdf?id=OveBaTtUAT](https://openreview.net/pdf?id=OveBaTtUAT)

### 4. Zero-Knowledge and Cryptographic Verification
11. Kang, D., et al. (2022). *Scaling up Trustless DNN Inference with Zero-Knowledge Proofs*. Proceedings of ACM CCS.

### 5. Technical Reports
12. Liu, K. Z. (2024). *Machine Unlearning in 2024*. Stanford University CS Technical Report. [https://ai.stanford.edu/~kzliu/files/unlearning.pdf](https://ai.stanford.edu/~kzliu/files/unlearning.pdf)

### 6. Regulatory and Legal References
13. General Data Protection Regulation (GDPR), Regulation (EU) 2016/679, Article 17 – Right to Erasure ("Right to be Forgotten").
14. California Consumer Privacy Act (CCPA), Cal. Civ. Code §1798.105 – Right to Delete.
15. Federal Trade Commission (FTC). *FTC v. Everalbum, Inc.* (2021). Enforcement action introducing algorithmic disgorgement.
