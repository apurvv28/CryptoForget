# Device Configuration and AI-Agent Resource Safety Rules

**Target device:** 16 GB RAM, Intel Core i5 12th generation, Intel Iris Xe, Windows + WSL2  
**Version:** 1.0  
**Priority:** Prevent OS instability, memory exhaustion and uncontrolled training.

## 1. Hardware assumptions

The exact i5 SKU is not yet known. 12th-generation i5 processors vary significantly in core count, power envelope and cooling. Therefore, do not hard-code a thread count based only on “i5-12th gen”.

Intel Iris Xe is not CUDA. The baseline must run on CPU. Do not install CUDA-only wheels or write code that assumes `torch.cuda.is_available()` will be true.

## 2. WSL2 memory configuration

Start conservatively. In Windows PowerShell:

```powershell
notepad $env:USERPROFILE\.wslconfig
```

Suggested initial configuration:

```ini
[wsl2]
memory=8GB
swap=2GB
processors=4
```

This is a conservative starting cap, not a universal optimum. Leave Windows enough RAM for the desktop, browser and other apps. Increase only after observing stable usage. Swap is emergency headroom and is much slower than RAM.

Apply:

```powershell
wsl --shutdown
```

Then restart WSL.

Check memory inside WSL:

```bash
free -h
nproc
```

Check Windows memory in Task Manager before long jobs.

## 3. CPU thread policy

Start with 2–4 PyTorch intra-op threads. Benchmark 2, 3 and 4; do not assume more threads are faster. Set inter-op threads to 1.

```python
import torch
torch.set_num_threads(3)
torch.set_num_interop_threads(1)
```

Set environment variables before importing numerical libraries where possible:

```bash
export OMP_NUM_THREADS=3
export MKL_NUM_THREADS=3
export OPENBLAS_NUM_THREADS=1
```

Do not run multiple shard training jobs concurrently on this laptop.

## 4. Hard resource guardrails

Initial safe limits:
- WSL memory cap: 8 GB.
- CPU workers: 1 training worker.
- PyTorch threads: 2–4.
- DataLoader workers: 0.
- Micro-batch: 1.
- Sequence length: 128 initially.
- Gradient accumulation: 1–4, only if stable.
- One model training process at a time.
- No parallel full-retraining baseline while SISA is training.
- Checkpoint frequency: after each slice, not every step.
- Disk free-space check before training.
- Stop if available RAM falls below 1.5 GB inside WSL or sustained swap activity begins.
- Stop if Windows becomes unresponsive or thermal throttling is sustained.

These are conservative project guardrails, not performance guarantees.

## 5. Safe training scheduler

Every training job must:
1. Read configured memory/CPU limits.
2. Check free disk space.
3. Check that no other training job is active.
4. Acquire an exclusive lock.
5. Load model with safe memory settings.
6. Log RSS and available memory periodically.
7. Stop at configured wall-time limit.
8. Save a recoverable checkpoint at slice boundaries.
9. Release lock on success/failure.
10. Never automatically retry indefinitely.

Use a manual approval gate before increasing memory, threads, sequence length, batch size or concurrency.

## 6. Example resource monitor

```python
import os
import time
import psutil

MAX_RSS_GB = 6.0
MIN_AVAILABLE_GB = 1.5

process = psutil.Process(os.getpid())

def check_resources():
    rss_gb = process.memory_info().rss / (1024 ** 3)
    available_gb = psutil.virtual_memory().available / (1024 ** 3)

    print({
        "rss_gb": round(rss_gb, 2),
        "available_gb": round(available_gb, 2)
    })

    if rss_gb > MAX_RSS_GB:
        raise RuntimeError("Training stopped: process RSS limit exceeded")

    if available_gb < MIN_AVAILABLE_GB:
        raise RuntimeError("Training stopped: available memory too low")
```

Install `psutil` and validate readings under WSL. Note that process RSS and system available memory are different measurements. The scheduler should also monitor cgroup/WSL limits where available.

## 7. Safe model settings

Initial experimental settings:
- SmolLM2-360M.
- FP32 baseline.
- CPU.
- Batch size 1.
- Sequence length 128.
- One shard trained at a time.
- Gradient checkpointing only if memory tests show it is needed; CPU recomputation may increase runtime.
- Avoid `torch.compile` for first baseline.
- Avoid loading four shard models into RAM simultaneously.
- Do not retain duplicate model copies in memory.
- Delete Python references and run garbage collection between shard jobs; this is not a substitute for process isolation.

A smaller model such as DistilGPT2 can be used to validate the pipeline before SmolLM2.

## 8. Process isolation

Prefer a dedicated worker process for each training job. The parent orchestrator should:
- Launch with explicit environment variables.
- Enforce a wall-time timeout.
- Capture logs.
- Monitor exit code and memory.
- Terminate gracefully on guardrail breach.
- Preserve last valid checkpoint.
- Never kill unrelated Windows/WSL processes.

Do not allow an AI agent to execute arbitrary shell commands with administrator privileges.

## 9. Disk and checkpoint safety

Before training:
- Check available disk space.
- Keep model cache, datasets and checkpoints in a dedicated project directory.
- Never write large datasets to the Windows system drive without checking space.
- Keep one known-good checkpoint and one latest checkpoint.
- Verify checkpoint file hashes after write.
- Use temporary file + atomic rename for checkpoint publication.
- Do not delete prior checkpoint until new checkpoint is verified.
- Use a documented cleanup command with dry-run mode.

## 10. Agent command policy

### Allowed without confirmation
- Read source files.
- Run unit tests.
- Run lint/type checks.
- Inspect CPU/RAM/disk.
- Run tiny synthetic tests under configured limits.
- Generate documentation.

### Require explicit human confirmation
- Download large model/dataset.
- Start full fine-tuning.
- Increase WSL memory/CPU cap.
- Increase sequence length/batch size/threads.
- Run multiple training processes.
- Delete checkpoints/datasets.
- Modify `.wslconfig`.
- Install system packages or alter OS configuration.
- Change signing keys or production secrets.
- Run migrations against non-test databases.

### Prohibited
- `sudo rm -rf` or broad destructive commands.
- Killing unknown processes.
- Disabling OS security.
- Unbounded loops/retries.
- Running training automatically after every code edit.
- Storing secrets in logs.
- Uploading private conversations to public services.
- Running GPU/CUDA setup scripts for an Intel-only baseline.

## 11. Safe experiment ladder

1. Environment smoke test, no model.
2. Tiny synthetic dataset, 10 steps.
3. Small model pipeline smoke test.
4. Single shard, one slice.
5. Single shard, three slices.
6. Two shards sequentially.
7. Four shards sequentially.
8. One deletion/retraining test.
9. Full benchmark only after manual review.

At every stage, record wall time, peak RSS, system available memory, disk usage and exit code.

## 12. Emergency stop

Stop the current training job if:
- Available memory below threshold.
- Process RSS above configured cap.
- Disk free space below safe reserve.
- WSL or Windows responsiveness degrades.
- Thermal/power throttling becomes sustained.
- Training produces NaN/Inf or runaway loss.
- Worker loses its exclusion-manifest lease.
- Tombstone epoch changes during job.

After stopping, preserve logs and last valid checkpoint. Do not automatically resume without checking whether the dataset exclusion manifest changed.


## 13. Resource-safe execution of RC1–RC3

### Merkle transparency log
- Merkle proof construction/verification is lightweight relative to model training, but must still be bounded.
- Batch log updates where appropriate; cap batch size and memory.
- Never rebuild an unbounded log tree in RAM on the laptop; persist nodes or use a bounded prototype dataset.
- Run proof benchmarks separately from SISA training.
- Use a test log for experiments; do not overwrite the research certificate log.

### Training-job race prevention
- Epoch/fencing checks are small database operations and must not be disabled to improve speed.
- Use one active training worker on the laptop.
- Worker heartbeat and lease timeouts must be bounded.
- On WSL restart, stale workers must be unable to publish; recover from database epoch and fencing token.
- A deletion epoch change causes safe abort, not an automatic high-memory retry loop.

### Cost-aware SISA
- Run shard/slice configurations sequentially, not concurrently.
- Use pilot configurations (2 shards, 2 slices) before 4×3; attempt 8 shards only after measured headroom.
- Capture peak RSS, wall time, disk and checkpoint size for every configuration.
- Stop a sweep when memory/disk guardrails trigger; record the run as resource-limited rather than silently omitting it.
- Never let an AI agent automatically expand the configuration grid or raise memory limits.
