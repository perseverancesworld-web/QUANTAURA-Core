"""Tests for cryptographic primitives."""

from quantaura.crypto.signatures import (
    canonicalize_payload,
    compute_payload_hash,
    generate_keypair,
    verify_signature,
)
from nacl.signing import SigningKey


def test_canonicalize_is_deterministic():
    payload = {"b": 2, "a": 1, "nested": {"z": 9, "y": 8}}
    a = canonicalize_payload(payload)
    b = canonicalize_payload(payload)
    assert a == b
    assert a == b'{"a":1,"b":2,"nested":{"y":8,"z":9}}'


def test_hash_is_stable():
    payload = {"amount": 500, "currency": "USD"}
    h1 = compute_payload_hash(payload)
    h2 = compute_payload_hash(payload)
    assert h1 == h2
    assert len(h1) == 64


def test_sign_and_verify_roundtrip():
    private_hex, public_hex = generate_keypair()
    payload = {"action": "TRANSFER_FUNDS", "amount": 42.0}
    sk = SigningKey(bytes.fromhex(private_hex))
    canonical = canonicalize_payload(payload)
    sig = sk.sign(canonical).signature.hex()
    assert verify_signature(public_hex, payload, sig) is True


def test_tampered_payload_fails():
    private_hex, public_hex = generate_keypair()
    payload = {"amount": 100}
    sk = SigningKey(bytes.fromhex(private_hex))
    sig = sk.sign(canonicalize_payload(payload)).signature.hex()
    payload["amount"] = 999999
    assert verify_signature(public_hex, payload, sig) is False
