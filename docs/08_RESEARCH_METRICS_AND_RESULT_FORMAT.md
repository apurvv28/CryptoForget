# Research Metrics, Calculation Protocol and Paper Result Format

**Version:** 1.0  
**Date:** 2026-11-02  
**Purpose:** Reproducible quantitative evaluation for the research paper.

## 1. Experimental principles

- Predefine research questions, hypotheses and metrics.
- Use identical initial pretrained checkpoint across comparable methods.
- Pin dataset, tokenizer, model revision and code.
- Use deterministic data partitioning and recorded seeds.
- Use at least 3 independent seeds for final claims where compute permits. If not, report the limitation and show per-run results.
- Use the same deletion requests across methods.
- Keep validation/test sets fixed and separate.
- Report mean, standard deviation and confidence intervals where appropriate.
- Report all failed runs and resource limits.
- Do not cherry-pick deletion positions or only report favorable shard cases.
- Report initial SISA cost as well as deletion cost.

## 2. Methods to compare

### M0 — Original model
Fine-tuned model on the complete consented dataset.

### M1 — Full retraining
Train from the same initial pretrained checkpoint on the retained dataset after deletion.

This is the clean reference for the deletion event.

### M2 — SISA
Retrain only affected shard(s), starting from checkpoint immediately before earliest affected slice.

### M3 — SISA without pre-tombstone enforcement (ablation)
Research-only controlled ablation to measure the protection provided by the exclusion barrier. Do not use this mode in real user workflows.

### M4 — Tombstone-only (ablation)
Exclude future use but do not retrain model. This is not model unlearning; it provides a baseline demonstrating the distinction.

### M5 — Optional random-retraining baseline
Retrain a randomly selected shard or use a non-lineage-aware strategy, if it adds a meaningful comparison.

## 3. Dataset and partition protocol

Document:
- Dataset source and license.
- Dataset version/hash.
- Number of subjects.
- Number of records/tokens.
- Language/domain.
- Preprocessing and deduplication.
- Consent simulation/collection procedure.
- Train/validation/test split.
- Subject-level split strategy.
- Number of records per shard/slice.
- Deletion target selection.

Prefer user/subject-level partitioning so all records from a subject are assigned consistently where possible. If a subject spans shards, report that explicitly and retrain all affected shards.

Use synthetic user IDs for public datasets. Do not use real chat logs without appropriate consent and governance.

## 4. Efficiency metrics

Let:
- `T_init_sisa` = initial time to train all SISA shards/slices.
- `T_full_del` = time to train clean full-retrain reference after deletion.
- `T_sisa_del` = time to retrain all affected SISA shard suffixes.
- `T_tombstone` = time from accepted request to committed exclusion barrier.
- `T_verify` = time to complete evidence verification.
- `T_total_sisa` = `T_tombstone + T_sisa_del + T_verify` (also report each component separately).

### Deletion speedup

`Speedup = T_full_del / T_sisa_del`

Use same timing boundary for numerator/denominator. Also report end-to-end speedup using `T_total_sisa` if comparing full workflows.

### Time saved percentage

`TimeSavedPct = ((T_full_del - T_sisa_del) / T_full_del) * 100`

Negative values are valid and must be reported if SISA is slower for a case.

### Training-step reduction

`StepReductionPct = ((Steps_full - Steps_sisa) / Steps_full) * 100`

Count optimizer steps, not micro-batches. Define what counts as a step.

### Compute cost
If energy measurement is available, measure joules/Wh using a documented instrument. Otherwise do not invent energy from CPU utilization. Report CPU time, wall time and peak memory separately.

### Initial cost amortization

For `N` deletion requests:

`TotalFullCost(N) = N * mean(T_full_del)`

`TotalSISACost(N) = T_init_sisa + N * mean(T_sisa_del)`

Break-even request count, if `T_full_del > T_sisa_del`:

`N_break_even = T_init_sisa / (T_full_del - T_sisa_del)`

This simplified formula ignores storage, inference and verification costs; report those separately and optionally extend total cost model.

## 5. Memory and system metrics

Record:
- Peak process RSS (GiB).
- Peak system available-memory drop (GiB).
- WSL memory limit.
- Swap used (GiB).
- CPU utilization (average and peak).
- Thread count.
- Disk usage before/after.
- Checkpoint size (GiB).
- Dataset size (GiB).
- Inference latency p50/p95.
- Training wall time.
- Training CPU time where available.

Never report only model parameter count as memory consumption.

## 6. Model utility metrics

For causal language modeling:
- Validation loss.
- Perplexity.
- Tokens/second.
- Generation latency.
- Task-specific accuracy/F1 if using a downstream task.
- Human evaluation only with a documented rubric and blinded protocol.

Perplexity:

`PPL = exp(mean_token_negative_log_likelihood)`

Use the same evaluation corpus, tokenizer, context length and token masking across methods. Do not compare perplexity values computed with different tokenizers or different evaluation sets.

Utility retention can be reported as:

`UtilityRetentionPct = (Utility_unlearned / Utility_original) * 100`

Only use this ratio for a metric where larger is better and denominator is nonzero. For loss/perplexity, report absolute and relative change instead.

## 7. Forgetting and privacy metrics

No single metric proves perfect forgetting. Use a suite:

### Membership inference
Report attack accuracy, ROC-AUC, TPR at fixed FPR and attack advantage. Define attack model, shadow data, target examples and non-member controls.

`MembershipAdvantage = TPR - FPR`

At a selected operating point, report exact FPR and TPR.

### Targeted extraction/memorization
Create a controlled canary or synthetic unique sequence dataset. Measure exact/partial extraction success before and after unlearning. Do not insert real personal data as canaries.

### Clean-retrain distance
Compare SISA-unlearned model to full-retrain reference:
- KL divergence over a fixed evaluation prompt set.
- Logit distribution distance.
- Output agreement.
- Task utility difference.

Example:

`MeanKL = mean_x KL(P_full(x) || P_sisa_unlearned(x))`

Document temperature and token alignment.

### Privacy/utility trade-off
Plot privacy attack metric against utility metric for each method/configuration.

Do not interpret low attack accuracy alone as proof of forgetting; a weak attack may simply be ineffective.

## 8. Pre-tombstone metrics

- Request-to-tombstone latency.
- Time to exclusion manifest publication.
- Number of active jobs fenced.
- Number of stale jobs prevented from commit.
- Number of post-request records excluded.
- Race-condition test pass rate.

`TombstoneLatency = tombstone_commit_timestamp - deletion_request_accepted_timestamp`

Report p50, p95 and maximum across requests.

## 9. Certificate and verifier metrics

- Signature verification success rate.
- Tamper detection rate.
- False acceptance rate.
- False rejection rate.
- Revocation detection.
- Unknown-ID handling.
- Verification latency p50/p95.
- Certificate generation latency.
- Public information disclosure audit.

Test:
1. Valid signed payload.
2. Altered payload.
3. Altered signature.
4. Wrong public key.
5. Unknown certificate.
6. Revoked certificate.
7. Pending request.
8. Completed request with missing evidence.
9. Stale/replayed evidence manifest.
10. Key rotation/historical verification.

For security tests, state the number of cases and expected/observed outcomes. Do not call a small unit-test suite a formal cryptographic proof.

## 10. SISA configuration matrix

Suggested initial matrix, constrained by device:
- Shards: 2, 4; 8 only if resource/time budget allows.
- Slices: 2, 3, 5.
- Deletion positions: early, middle, late.
- Affected shard fraction: 1 shard, multiple shards, all shards.
- Deletion sizes: one record, 1%, 5% of subject records.
- Seeds: at least 3 for final selected conditions.

Use a pilot to reduce the full matrix if CPU budget is insufficient. Do not run all configurations concurrently on the 16 GB laptop.

## 11. Result table formats

### Table A — Main efficiency results

| Method | Shards | Slices | Initial train (min) | Deletion train (min) | End-to-end deletion (min) | Speedup | Time saved (%) |
|---|---:|---:|---:|---:|---:|---:|---:|
| Full retrain | — | — | — | — | — | 1.00× | 0 |
| SISA | 2 | 3 | — | — | — | — | — |
| SISA | 4 | 3 | — | — | — | — | — |

### Table B — Resource results

| Method | Peak RSS (GiB) | Swap peak (GiB) | CPU avg (%) | CPU peak (%) | Disk/checkpoints (GiB) | Inference p95 (ms) |
|---|---:|---:|---:|---:|---:|---:|
| Full retrain | — | — | — | — | — | — |
| SISA 2×3 | — | — | — | — | — | — |
| SISA 4×3 | — | — | — | — | — | — |

### Table C — Utility and forgetting

| Method | Validation loss | Perplexity | Task score | MIA AUC | MIA advantage | Mean KL to clean retrain |
|---|---:|---:|---:|---:|---:|---:|
| Original | — | — | — | — | — | — |
| Full retrain | — | — | — | — | — | 0 |
| SISA unlearned | — | — | — | — | — | — |
| Tombstone only | — | — | — | — | — | — |

### Table D — Tombstone and certificate

| Test | N | Pass | Fail | p50 latency | p95 latency |
|---|---:|---:|---:|---:|---:|
| Tombstone race | — | — | — | — | — |
| Stale job fencing | — | — | — | — | — |
| Signature tamper | — | — | — | — | — |
| Revocation | — | — | — | — | — |
| Public verifier privacy | — | — | — | — | — |

## 12. Statistical reporting

For each condition:
- Show individual seed values.
- Mean and standard deviation.
- 95% confidence interval where sample size supports it.
- Paired comparison where same deletion requests/seeds are used.
- Report effect size, not only p-value.
- Use appropriate tests and state assumptions.
- Correct for multiple comparisons if conducting many hypothesis tests.
- Do not claim statistical significance from one run.

For small n, show raw points and avoid overstating confidence intervals.

## 13. Paper structure

1. Abstract.
2. Introduction and motivation.
3. Background: machine unlearning, SISA, tombstoning, digital signatures.
4. Related work.
5. Threat model and system requirements.
6. Proposed architecture.
7. SISA and pre-tombstoning algorithms.
8. Evidence manifest and certificate protocol.
9. Experimental setup.
10. Results.
11. Ablation studies.
12. Security/privacy analysis.
13. Limitations and ethical considerations.
14. Conclusion and future work.

## 14. Cherry-on-top research contributions

### A. Deletion Transparency Log
Maintain an append-only Merkle tree over certificate issuance/revocation events. Publish signed tree roots periodically. A verifier can check inclusion and consistency proofs. This adds tamper-evident history without putting user data on a blockchain.

### B. Evidence Manifest with policy version
Each certificate commits to a canonical manifest containing checks, verifier versions, timestamps and artifact references. The certificate signs the manifest digest. This makes the exact meaning of “completed” auditable and versioned.

### C. Job-fencing and deletion-race protocol
Research the race where a training worker has already loaded data when deletion is requested. Use exclusion epochs and commit-time fencing. Measure stale-job rejection and request-to-exclusion latency.

### D. Multi-dimensional deletion assurance scorecard
Do not compress everything into a misleading single score. Show separate dimensions:
- Source-data status.
- Derived-data status.
- Future-use exclusion.
- Model-unlearning status.
- Old artifact retirement.
- Backup status.
- Cryptographic authenticity.

### E. Cost-aware SISA policy
Investigate how shard count, slice count and deletion distribution affect initial cost, unlearning cost, storage and inference. Derive an empirical break-even point for your workload.

### F. Optional independent verifier
Provide a separate verifier tool that downloads a public certificate, checks signature/key/revocation and validates manifest consistency. This reduces dependence on the UI but still trusts the evidence-generation process.

## 15. Reproducibility package

Release, subject to dataset/model licenses and privacy:
- Source code.
- Environment lockfiles.
- Model revision.
- Dataset description and permitted dataset or download instructions.
- Experiment configs.
- Random seeds.
- Run manifests.
- Raw aggregate metrics.
- Analysis scripts.
- Certificate test vectors.
- Public test signing key only (never real private key).
- Synthetic sample certificates.
- Threat model.
- Known limitations.

## 16. Claims checklist for paper

Before submission:
- [ ] Do not call a signature proof of deletion.
- [ ] Distinguish tombstoning, source deletion and model unlearning.
- [ ] Include initial SISA cost.
- [ ] Include inference overhead.
- [ ] Include backup and derived-data scope.
- [ ] Compare to clean retraining.
- [ ] Report failed/negative results.
- [ ] Explain limitations of empirical forgetting metrics.
- [ ] Include threat model and trust assumptions.
- [ ] Do not claim legal compliance without legal review.


## 17. Dedicated research evaluation for the three core contributions

### RC1 — Merkle transparency log metrics
Measure:
- Append throughput (events/second).
- Append latency p50/p95.
- Inclusion proof generation latency.
- Inclusion proof verification latency.
- Consistency proof generation/verification latency.
- Proof byte size.
- Signed tree-head verification success.
- Tamper detection rate.
- Fork/rollback detection in simulated adversarial scenarios.
- Storage growth per 1,000 events.

Suggested result table:

| Log size | Append p95 (ms) | Inclusion proof (ms) | Verify proof (ms) | Proof size (bytes) | Tamper cases detected / total |
|---:|---:|---:|---:|---:|---:|
| 1,000 | — | — | — | — | — |
| 10,000 | — | — | — | — | — |
| 100,000 | — | — | — | — | — |

State the threat model and trusted tree-head distribution assumptions. Merkle inclusion alone does not prevent an operator from showing different roots to different users; consistency monitoring, witnesses or gossip are needed to detect split views.

### RC2 — Training-job race prevention metrics
Test deletion arrival at:
1. Before dataset manifest creation.
2. During dataset loading.
3. During a training slice.
4. During checkpoint serialization.
5. After checkpoint write but before publish.
6. During model promotion.
7. After worker lease expiry.
8. During worker/network partition.

Measure:
- Stale-job rejection rate.
- Number of tombstoned records committed after request (target zero).
- Request-to-epoch-commit latency.
- Request-to-worker-stop latency.
- Abort/restart wall time.
- False abort rate (jobs invalidated without relevant exclusion change).
- Race-test pass rate.

Definitions:
`StaleJobRejectionRate = stale_jobs_rejected / stale_jobs_attempting_commit`

`PostRequestCommitCount = count(tombstoned_records included in artifacts committed after tombstone epoch)`

Target for the controlled test harness: `PostRequestCommitCount = 0`. Report actual count and test volume.

Suggested table:

| Race point | Trials | Stale commit attempts | Rejected | Stale commits | p95 fence latency |
|---|---:|---:|---:|---:|---:|
| Dataset load | — | — | — | — | — |
| Mid-slice | — | — | — | — | — |
| Checkpoint write | — | — | — | — | — |
| Model promotion | — | — | — | — | — |
| Lease expiry | — | — | — | — | — |

### RC3 — Cost-aware SISA metrics and configuration selection

Independent variables:
- Shard count K.
- Slices per shard S.
- Deletion position (early/middle/late).
- Affected shard fraction.
- Deleted record/subject fraction.
- Dataset size.
- Model size.
- Hardware profile.

Dependent variables:
- Initial training time.
- Deletion retraining time.
- Total lifecycle cost.
- Checkpoint storage.
- Peak RAM and CPU time.
- Model utility.
- Forgetting/privacy metrics.
- Inference latency and memory.

Use Pareto analysis across at least:
- Minimize deletion retraining time.
- Minimize initial training cost.
- Minimize checkpoint storage.
- Minimize inference latency.
- Maximize utility.
- Improve forgetting metrics (with explicitly defined direction).

A configuration is Pareto-dominated if another configuration is no worse in all selected objectives and strictly better in at least one. Report the Pareto frontier rather than inventing arbitrary weights.

If a scalar score is needed for a deployment scenario, publish the weights and conduct sensitivity analysis. Do not present that score as universally optimal.

#### Break-even analysis
For a workload with N deletion requests:

`TotalFullCost(N) = N * C_full_delete`

`TotalSISACost(N) = C_initial_sisa + N * C_sisa_delete + C_storage + C_inference_overhead`

For time-only simplified analysis, omit unlike units and state the simplification. For a more complete cost model, convert measured CPU time, storage and inference into a documented common cost unit or report each separately.

#### Suggested configuration table

| K shards | S slices | Initial train (min) | Mean deletion (min) | Checkpoint storage (GiB) | Utility score | Forgetting metric | Inference p95 (ms) | Peak RAM (GiB) |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2 | 2 | — | — | — | — | — | — | — |
| 2 | 3 | — | — | — | — | — | — | — |
| 4 | 3 | — | — | — | — | — | — | — |
| 4 | 5 | — | — | — | — | — | — | — |

### Integrated contribution ablations

| Variant | Merkle log | Epoch/fencing | Cost-aware selector | Purpose |
|---|---|---|---|---|
| Base SISA | No | No | No | ML baseline |
| + Tombstone | No | Basic | No | Exclusion behavior |
| + Race protection | No | Yes | No | Concurrency safety |
| + Merkle evidence | Yes | Yes | No | Auditability |
| Full framework | Yes | Yes | Yes | Combined system |

For paper clarity, report that the Merkle log improves auditability, job fencing improves correctness under concurrency, and cost-aware selection improves configuration choice. Do not claim any of these independently improves neural forgetting unless experiments demonstrate that effect.

## 18. Updated paper contribution statement

The paper may claim the following contributions if implemented and evaluated:
1. A user-facing privacy-aware conversational AI architecture integrating consent, data lineage, pre-tombstoning and SISA unlearning.
2. A race-safe deletion protocol using exclusion epochs and commit-time fencing to prevent stale training artifacts from being published after a deletion request.
3. A Merkle-based append-only deletion transparency log with signed tree heads and independently verifiable inclusion/consistency proofs.
4. A cost-aware SISA configuration study that characterizes trade-offs among initial training cost, deletion retraining, checkpoint storage, model utility, forgetting and inference latency.
5. An empirical evaluation against clean full retraining with explicit limitations of cryptographic and model-level deletion assurance.
