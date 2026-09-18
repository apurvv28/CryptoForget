import os
from pathlib import Path

# Project Base Directory
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Models & Data Locations
MODELS_DIR = Path(os.getenv("MODELS_DIR", str(PROJECT_ROOT / "models")))
DATA_DIR = Path(os.getenv("DATA_DIR", str(PROJECT_ROOT / "data" / "raw" / "MINDsmall_train")))

# Database Configuration (Defaults to SQLite for local development, extensible to CockroachDB / PostgreSQL)
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{PROJECT_ROOT / 'crypto_forget.db'}")

# MLOps & Tracking (Formatted as compliant SQLite URI for MLflow tracking & model registry)
MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", f"sqlite:///{PROJECT_ROOT / 'mlflow.db'}")
MODEL_VERSION = os.getenv("MODEL_VERSION", "dev")

# Cryptographic Verification Settings
ECDSA_KEY_DIR = Path(os.getenv("ECDSA_KEY_DIR", str(PROJECT_ROOT / "crypto_keys")))
ECDSA_PRIVATE_KEY_PATH = ECDSA_KEY_DIR / "private_key.pem"
ECDSA_PUBLIC_KEY_PATH = ECDSA_KEY_DIR / "public_key.pem"

# SISA Unlearning Hyperparameters
SISA_NUM_SHARDS = int(os.getenv("SISA_NUM_SHARDS", "5"))
SISA_NUM_SLICES = int(os.getenv("SISA_NUM_SLICES", "2"))

# Fusion & Profile Parameters
ALPHA = float(os.getenv("ALPHA", "0.5"))
SHORT_TERM_WINDOW_HOURS = float(os.getenv("SHORT_TERM_WINDOW_HOURS", "24"))
DECAY_RATE = float(os.getenv("DECAY_RATE", "0.05"))
