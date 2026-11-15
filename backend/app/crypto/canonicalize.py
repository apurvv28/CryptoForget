"""
RFC 8785 JSON Canonicalization Scheme (JCS) and SHA-256 Digest Utility.

Provides deterministic, bit-for-bit reproducible JSON serialization per RFC 8785
and Doc 01 (§10) & Doc 05 (§11).
"""

import hashlib
import json
from typing import Any


def canonicalize(data: Any) -> bytes:
    """
    Serializes a Python dict/object to canonical JSON bytes per RFC 8785:
    - Object keys sorted lexicographically by UTF-16 code units (equivalent to Unicode code point for ASCII).
    - No whitespace between tokens (separators=(',', ':')).
    - UTF-8 encoding without BOM.
    - Deterministic float/int formatting.
    """
    def _sort_keys(obj: Any) -> Any:
        if isinstance(obj, dict):
            return {k: _sort_keys(v) for k, v in sorted(obj.items(), key=lambda item: item[0])}
        elif isinstance(obj, list):
            return [_sort_keys(item) for item in obj]
        return obj

    sorted_data = _sort_keys(data)
    json_str = json.dumps(
        sorted_data,
        ensure_ascii=False,
        allow_nan=False,
        indent=None,
        separators=(",", ":"),
    )
    return json_str.encode("utf-8")


def digest_sha256(data: bytes | str | Any) -> str:
    """
    Computes a hexadecimal SHA-256 digest over bytes or a canonicalized JSON object.
    """
    if isinstance(data, bytes):
        raw_bytes = data
    elif isinstance(data, str):
        raw_bytes = data.encode("utf-8")
    else:
        raw_bytes = canonicalize(data)

    return hashlib.sha256(raw_bytes).hexdigest()
