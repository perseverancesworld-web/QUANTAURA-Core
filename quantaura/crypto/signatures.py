"""Canonical JSON hashing and Ed25519 signature verification.

Ensures payloads cannot be tampered with in transit.
"""

from __future__ import annotations

import hashlib
import json
from typing import Tuple

from nacl.exceptions import BadSignatureError
from nacl.signing import SigningKey, VerifyKey


def canonicalize_payload(payload: dict) -> bytes:
    """Serialize a dictionary into a deterministic, sorted JSON byte string."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def compute_payload_hash(payload: dict) -> str:
    """Compute the SHA-256 hash of a canonicalized payload."""
    canonical_bytes = canonicalize_payload(payload)
    return hashlib.sha256(canonical_bytes).hexdigest()


def verify_signature(public_key_hex: str, payload: dict, signature_hex: str) -> bool:
    """Verify an Ed25519 signature against a canonical payload."""
    try:
        verify_key = VerifyKey(bytes.fromhex(public_key_hex))
        canonical_bytes = canonicalize_payload(payload)
        verify_key.verify(canonical_bytes, bytes.fromhex(signature_hex))
        return True
    except (BadSignatureError, ValueError, TypeError):
        return False


def generate_keypair() -> Tuple[str, str]:
    """Generate a fresh Ed25519 keypair.

    Returns:
        (private_key_hex, public_key_hex)
    """
    signing_key = SigningKey.generate()
    private_hex = signing_key.encode().hex()
    public_hex = signing_key.verify_key.encode().hex()
    return private_hex, public_hex
