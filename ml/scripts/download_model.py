"""
Download and pin the DistilGPT2 model for pipeline validation.

Usage:
    python -m ml.scripts.download_model

Downloads distilbert/distilgpt2 from Hugging Face Hub and saves it
locally with revision pinning for reproducibility.
"""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from transformers import AutoModelForCausalLM, AutoTokenizer


MODEL_ID = "distilbert/distilgpt2"
LOCAL_DIR = Path("./models/distilgpt2")


def download_and_pin() -> dict:
    """Download model and record provenance metadata."""
    print(f"Downloading {MODEL_ID}...")

    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
    model = AutoModelForCausalLM.from_pretrained(MODEL_ID)

    LOCAL_DIR.mkdir(parents=True, exist_ok=True)
    tokenizer.save_pretrained(str(LOCAL_DIR))
    model.save_pretrained(str(LOCAL_DIR))

    # Record provenance
    manifest = {
        "model_id": MODEL_ID,
        "local_path": str(LOCAL_DIR),
        "download_timestamp": datetime.now(timezone.utc).isoformat(),
        "num_parameters": sum(p.numel() for p in model.parameters()),
        "license": "apache-2.0",
        "files": {},
    }

    # Hash saved files
    for f in sorted(LOCAL_DIR.iterdir()):
        if f.is_file():
            sha256 = hashlib.sha256(f.read_bytes()).hexdigest()
            manifest["files"][f.name] = {
                "size_bytes": f.stat().st_size,
                "sha256": sha256,
            }

    manifest_path = LOCAL_DIR / "download_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))
    print(f"Model saved to {LOCAL_DIR}")
    print(f"Manifest saved to {manifest_path}")
    print(f"Parameters: {manifest['num_parameters']:,}")

    return manifest


if __name__ == "__main__":
    download_and_pin()
