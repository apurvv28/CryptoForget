import base64
from pathlib import Path
from typing import Tuple

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec

from src.config import ECDSA_KEY_DIR, ECDSA_PRIVATE_KEY_PATH, ECDSA_PUBLIC_KEY_PATH


class ECDSAService:
    """ECDSA SECP256k1 digital signature service for signing and verifying deletion certificates."""

    def __init__(
        self,
        private_key_path: Path = ECDSA_PRIVATE_KEY_PATH,
        public_key_path: Path = ECDSA_PUBLIC_KEY_PATH,
    ) -> None:
        self.private_key_path = Path(private_key_path)
        self.public_key_path = Path(public_key_path)
        self.private_key, self.public_key = self._load_or_generate_keys()

    def _load_or_generate_keys(self) -> Tuple[ec.EllipticCurvePrivateKey, ec.EllipticCurvePublicKey]:
        """Loads existing PEM keypair or generates a new SECP256k1 keypair."""
        if self.private_key_path.exists() and self.public_key_path.exists():
            with open(self.private_key_path, "rb") as f:
                private_key = serialization.load_pem_private_key(f.read(), password=None)
            with open(self.public_key_path, "rb") as f:
                public_key = serialization.load_pem_public_key(f.read())
            return private_key, public_key

        # Generate new keypair
        private_key = ec.generate_private_key(ec.SECP256K1())
        public_key = private_key.public_key()

        # Save to disk
        self.private_key_path.parent.mkdir(parents=True, exist_ok=True)

        with open(self.private_key_path, "wb") as f:
            f.write(
                private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption(),
                )
            )

        with open(self.public_key_path, "wb") as f:
            f.write(
                public_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo,
                )
            )

        return private_key, public_key

    def get_public_key_pem(self) -> str:
        """Returns public key formatted as PEM string."""
        pem_bytes = self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        return pem_bytes.decode("utf-8")

    def sign_payload(self, payload: str) -> str:
        """Signs a text payload using private key and returns base64 encoded ECDSA signature."""
        signature_bytes = self.private_key.sign(
            payload.encode("utf-8"),
            ec.ECDSA(hashes.SHA256()),
        )
        return base64.b64encode(signature_bytes).decode("utf-8")

    @staticmethod
    def verify_signature(payload: str, signature_b64: str, public_key_pem: str) -> bool:
        """Verifies an ECDSA signature against a payload using a public key PEM string."""
        try:
            public_key = serialization.load_pem_public_key(public_key_pem.encode("utf-8"))
            signature_bytes = base64.b64decode(signature_b64)
            public_key.verify(
                signature_bytes,
                payload.encode("utf-8"),
                ec.ECDSA(hashes.SHA256()),
            )
            return True
        except (InvalidSignature, Exception):
            return False


# Singleton instance
_ecdsa_service_instance = None


def get_ecdsa_service() -> ECDSAService:
    global _ecdsa_service_instance
    if _ecdsa_service_instance is None:
        _ecdsa_service_instance = ECDSAService()
    return _ecdsa_service_instance
