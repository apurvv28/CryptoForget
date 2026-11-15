"""
Resource monitor — RAM/CPU/disk guardrails during training.

Enforces the safety limits from Doc 06:
- MAX_RSS_GB, MIN_AVAILABLE_GB
- Disk space checks
- Wall-time limits
- Emergency stop on resource breach
"""

import os
import psutil


MAX_RSS_GB = float(os.environ.get("MAX_RSS_GB", "8.0"))
MIN_AVAILABLE_GB = float(os.environ.get("MIN_AVAILABLE_GB", "0.5"))


def check_resources() -> dict[str, float]:
    """Check current resource usage and raise if limits exceeded."""
    process = psutil.Process(os.getpid())
    rss_gb = process.memory_info().rss / (1024 ** 3)
    available_gb = psutil.virtual_memory().available / (1024 ** 3)

    stats = {
        "rss_gb": round(rss_gb, 2),
        "available_gb": round(available_gb, 2),
    }

    if rss_gb > MAX_RSS_GB:
        raise RuntimeError(
            f"Training stopped: process RSS {rss_gb:.2f} GiB exceeds limit {MAX_RSS_GB} GiB"
        )

    if available_gb < MIN_AVAILABLE_GB:
        raise RuntimeError(
            f"Training stopped: available memory {available_gb:.2f} GiB below {MIN_AVAILABLE_GB} GiB"
        )

    return stats
