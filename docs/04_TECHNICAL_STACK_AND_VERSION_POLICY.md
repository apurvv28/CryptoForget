# Technical Stack, Version Policy and Compatibility Matrix

**Version:** 1.0  
**Date checked:** 2026-11-02  
**Target:** Windows 11 + WSL2, Ubuntu LTS, 16 GB RAM, Intel Core i5 12th gen, Iris Xe

## 1. Version policy

“Latest” changes continuously and latest does not always mean compatible or reproducible. For a research paper, use the latest stable compatible release that passes the full test suite, then freeze exact versions in lockfiles and record them in every experiment.

As of 2026-11-02, Python.org lists Python 3.15.2 as the newest general release, but the research stack should use Python 3.12.16 as a conservative compatibility baseline until the exact PyTorch CPU wheel, Transformers, Tokenizers and Datasets combination is verified. The PyTorch Windows documentation currently documents Python support through 3.12; WSL/Linux support can differ, so do not infer compatibility from the Windows page. Node.js 26 is listed as LTS (while 27 is Alpha), React 19.3 is the latest React blog release, and PostgreSQL 18.6 is the current supported major/minor shown by PostgreSQL. PyTorch's install selector should be used to select the currently tested Stable CPU build. These are point-in-time references, not permanent pins. Always run compatibility tests and freeze exact patch versions before experiments.

## 2. Proposed stack

| Layer | Technology | Version policy / baseline |
|---|---|---|
| OS | Windows 11 + WSL2 | Current supported Windows build; WSL updated |
| Linux | Ubuntu 24.04 LTS | Latest security updates |
| Python | CPython | 3.12.16 recommended compatibility baseline; newer Python branches exist, but verify PyTorch/Transformers wheel support before adopting them |
| Frontend runtime | Node.js | 26 LTS (or latest supported LTS at lock time); avoid Alpha/Current for reproducible deployment |
| Frontend | React | 19.3 stable (verify ecosystem compatibility at lock time) |
| Build tool | Vite | Current stable |
| UI | Tailwind CSS | Current stable |
| API | FastAPI | Current stable |
| ASGI server | Uvicorn | Current stable |
| Validation | Pydantic | Version supported by FastAPI |
| ML | PyTorch | CPU wheel compatible with Python/OS |
| NLP | Transformers | Pin exact compatible release |
| Dataset | Datasets | Pin exact compatible release |
| Tokenization | Tokenizers | Resolver-compatible version |
| Model | SmolLM2-360M | Pin immutable model revision/commit |
| DB | PostgreSQL | 18.6 current supported major/minor at check date; use latest minor of supported major |
| ORM/migrations | SQLAlchemy + Alembic | Current compatible stable |
| Queue | Redis | Supported stable release |
| Worker | RQ or Celery | Choose one; avoid unnecessary complexity |
| Crypto | cryptography | Current stable |
| QR | qrcode + Pillow | Current stable |
| Tests | pytest | Current stable |
| API tests | httpx | Compatible with FastAPI |
| Containers | Docker Desktop + WSL2 backend | Current stable |
| Observability | Prometheus/OpenTelemetry (optional) | Add only after MVP |

## 3. Official sources to check

- Python releases: https://www.python.org/downloads/ (3.15.2 newest general release at check date; choose 3.12.16 for conservative ML compatibility)
- PyTorch install selector: https://pytorch.org/get-started/locally/ (choose Stable + Linux + Pip + CPU; verify Python support)
- Transformers: https://huggingface.co/docs/transformers/index
- Hugging Face model card: https://huggingface.co/HuggingFaceTB/SmolLM2-360M
- FastAPI: https://fastapi.tiangolo.com/
- React release blog: https://react.dev/blog/ (React 19.3 listed 2026-09-09)
- Node.js releases: https://nodejs.org/en/about/previous-releases (Node 26 LTS; Node 27 Alpha at check date)
- PostgreSQL versioning: https://www.postgresql.org/support/versioning/ (PostgreSQL 18.6 listed current at check date)
- Redis: https://redis.io/docs/latest/
- Python cryptography: https://cryptography.io/en/latest/
- RFC 8785 JSON Canonicalization: https://www.rfc-editor.org/rfc/rfc8785
- Ed25519 standard: https://www.rfc-editor.org/rfc/rfc8032
- WSL configuration: https://learn.microsoft.com/en-us/windows/wsl/wsl-config

## 4. Installation sequence

Inside WSL Ubuntu:

```bash
sudo apt update
sudo apt upgrade
sudo apt install -y python3.12 python3.12-venv python3-pip \
  build-essential git curl jq

python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

Install PyTorch using the official selector and select Linux + Pip + CPU. Do not copy a CUDA command for Iris Xe.

Then install compatible packages from a locked requirements file:

```bash
pip install fastapi uvicorn pydantic sqlalchemy alembic \
  psycopg[binary] redis rq transformers datasets \
  accelerate safetensors cryptography qrcode[pil] \
  pytest httpx
```

This is a bootstrap command only. For a reproducible release, use pinned versions and a generated lock file after testing.

Frontend:

```bash
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install
```

Use the current supported Node LTS. Commit the lockfile.

## 5. Model pinning

Do not load a moving `main` branch for final experiments. Resolve the model repository to a specific commit hash and record:
- repository ID
- commit hash
- tokenizer revision
- config hash
- license
- download date
- file hashes where practical

Check the current model card and license before redistribution or deployment.

## 6. CPU training requirements

- CPU-only PyTorch.
- No CUDA dependency.
- Verify CPU features and PyTorch build.
- Use FP32 as baseline.
- Test BF16 only if CPU and framework support are confirmed; report it as a separate condition.
- Do not assume Intel Iris Xe is available to PyTorch as a CUDA device.
- Intel GPU acceleration is optional research only and must not be required for correctness.

## 7. Reproducibility manifest

Every run should write a `run_manifest.json` with:
- git commit
- Python version
- OS/kernel
- PyTorch version
- Transformers version
- model commit
- dataset version and manifest hash
- tokenizer revision
- seed
- shard/slice counts
- optimizer/scheduler settings
- sequence length
- effective batch size
- thread count
- start/end time
- host memory limit
- peak RSS
- output artifact hashes

## 8. Upgrade policy

- Do not upgrade dependencies during an experiment series.
- Upgrade in a separate branch.
- Run unit, integration, cryptographic and ML regression tests.
- Re-run a small benchmark.
- Record changed versions.
- Never overwrite archived environment metadata.


## 9. Version facts checked on 2026-11-02

- Python.org lists Python 3.15.2 as the newest general release; Python 3.12.16 is a conservative choice for this ML stack pending wheel compatibility checks. Source: https://www.python.org/downloads/
- PyTorch's official selector labels Stable as the currently tested/supported build and offers CPU as a compute platform. Select the exact command there rather than copying a CUDA command. Source: https://pytorch.org/get-started/locally/
- React's official blog lists React 19.3 (September 9, 2026). Source: https://react.dev/blog
- Node.js release page lists Node 26 as LTS and Node 27 as Alpha at the check date. Production should use an LTS line. Source: https://nodejs.org/en/about/previous-releases
- PostgreSQL versioning page lists 18.6 as supported/current. Source: https://www.postgresql.org/support/versioning/
- WSL `.wslconfig` controls WSL2 VM memory and processor allocation; settings apply after WSL restart. Source: https://learn.microsoft.com/en-us/windows/wsl/wsl-config
- RFC 8785 describes deterministic JSON canonicalization for repeatable hashing/signing. Source: https://www.rfc-editor.org/rfc/rfc8785

Because PyTorch's official selector and ecosystem compatibility can change faster than documentation, do not hard-code an unverified PyTorch version in this plan. Capture the resolved version with `python -c "import torch; print(torch.__version__)"` and preserve the lockfile.


## 10. Additional technical components for the three research contributions

### Merkle transparency log
Recommended initial implementation:
- A small Python transparency-log service/module.
- SHA-256 with domain-separated leaf and internal-node hashing.
- RFC 6962-style Merkle inclusion/consistency proof design, or a clearly specified equivalent.
- Ed25519-signed tree heads.
- PostgreSQL append-only event table for prototype; export signed tree heads and proofs.
- A separate public verification library/endpoint.

Do not invent a new Merkle construction. Select a documented construction, publish test vectors and verify against an independent implementation where feasible. A database table alone is not a cryptographic transparency log; signed roots and proof verification are required.

### Training-job race prevention
- PostgreSQL transaction for tombstone + epoch increment.
- Immutable dataset manifest stored by content digest.
- Worker lease/fencing token in job metadata.
- Redis/RQ or Celery may deliver jobs, but database epoch is authoritative.
- Worker validates epoch before reading and before publishing.
- Atomic model manifest pointer switch only after all checks pass.

### Cost-aware SISA
- Experiment configuration files (YAML/JSON) for shard/slice grids.
- PyTorch profiler and process/system telemetry for CPU/RAM.
- CSV/Parquet result store and Python analysis notebooks.
- Pareto-frontier analysis with pandas/numpy/scipy/matplotlib.
- Store inference benchmark and checkpoint size for each configuration.

Additional official references:
- Certificate Transparency RFC 9162 (Merkle inclusion/consistency concepts): https://www.rfc-editor.org/rfc/rfc9162
- RFC 6962 (historical Merkle audit proof design): https://www.rfc-editor.org/rfc/rfc6962
- RFC 8785 canonical JSON: https://www.rfc-editor.org/rfc/rfc8785
- Python cryptography: https://cryptography.io/en/latest/

Exact package versions for any transparency-log library must be resolved, tested and locked separately; do not depend on an unmaintained or unaudited package merely to save implementation time.
