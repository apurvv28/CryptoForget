"""
Ed25519 Digital Signature & Key Management Service — Phase 7 (RC1).

Implements asymmetric Ed25519 signing and verification per RFC 8032,
Doc 01 (§10), and Doc 05 (§11).
"""

import base64
import json
from pathlib import Path
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519

from app.crypto.canonicalize import canonicalize, digest_sha256


class KeyManager:
    """Manages persistent Ed25519 signing keys, rotation, and public discovery."""

    def __init__(self, keys_dir: str = "./data/keys", key_id: str = "key_2026_01"):
        self.keys_dir = Path(keys_dir)
        self.keys_dir.mkdir(parents=True, exist_ok=True)
        self.active_key_id = key_id
        self.private_key_path = self.keys_dir / f"{key_id}_private.pem"
        self.public_key_path = self.keys_dir / f"{key_id}_public.pem"
        self.keys_registry_path = self.keys_dir / "verification_keys.json"

        self._private_key: ed25519.Ed25519PrivateKey | None = None
        self._public_key: ed25519.Ed25519PublicKey | None = None
        self._load_or_generate_keys()

    def _load_or_generate_keys(self) -> None:
        """Loads existing active keypair or generates a new one."""
        if self.private_key_path.exists() and self.public_key_path.exists():
            with open(self.private_key_path, "rb") as f:
                self._private_key = serialization.load_pem_private_key(f.read(), password=None)  # type: ignore
            with open(self.public_key_path, "rb") as f:
                self._public_key = serialization.load_pem_public_key(f.read())  # type: ignore
        else:
            self._private_key = ed25519.Ed25519PrivateKey.generate()
            self._public_key = self._private_key.public_key()

            # Save PEM files
            priv_bytes = self._private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption(),
            )
            pub_bytes = self._public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )
            self.private_key_path.write_bytes(priv_bytes)
            self.public_key_path.write_bytes(pub_bytes)

        # Update verification keys registry
        self._update_public_registry()

    def get_public_key_b64(self) -> str:
        """Returns base64-encoded raw 32-byte Ed25519 public key."""
        raw_pub = self._public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        return base64.b64encode(raw_pub).decode("utf-8")

    def _update_public_registry(self) -> None:
        """Maintains the /.well-known/verification-keys.json registry."""
        registry: dict[str, Any] = {"keys": []}
        if self.keys_registry_path.exists():
            try:
                registry = json.loads(self.keys_registry_path.read_text())
            except Exception:
                registry = {"keys": []}

        # Check if active key already recorded
        existing_ids = {k["key_id"] for k in registry.get("keys", [])}
        if self.active_key_id not in existing_ids:
            registry["keys"].append(
                {
                    "key_id": self.active_key_id,
                    "algorithm": "Ed25519",
                    "public_key_b64": self.get_public_key_b64(),
                    "status": "active",
                }
            )
            self.keys_registry_path.write_text(json.dumps(registry, indent=2))

    def get_verification_keys_doc(self) -> dict[str, Any]:
        """Returns the public key discovery document per Doc 01 §11."""
        if self.keys_registry_path.exists():
            return json.loads(self.keys_registry_path.read_text())
        return {
            "keys": [
                {
                    "key_id": self.active_key_id,
                    "algorithm": "Ed25519",
                    "public_key_b64": self.get_public_key_b64(),
                    "status": "active",
                }
            ]
        }

    def sign(self, data: bytes) -> tuple[str, str]:
        """
        Signs arbitrary bytes with the active Ed25519 private key.
        Returns: (base64_signature, key_id)
        """
        assert self._private_key is not None
        sig = self._private_key.sign(data)
        return base64.b64encode(sig).decode("utf-8"), self.active_key_id

    def verify(self, data: bytes, signature_b64: str, public_key_b64: str | None = None) -> bool:
        """
        Verifies an Ed25519 signature over data bytes using public key or active key.
        """
        try:
            sig_bytes = base64.b64decode(signature_b64)
            if public_key_b64 is not None:
                pub_raw = base64.b64decode(public_key_b64)
                verifier = ed25519.Ed25519PublicKey.from_public_bytes(pub_raw)
            else:
                verifier = self._public_key

            assert verifier is not None
            verifier.verify(sig_bytes, data)
            return True
        except (InvalidSignature, ValueError, Exception):
            return False


# Global singleton
key_manager = KeyManager()
