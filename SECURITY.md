# Security Policy

## Supported versions

| Version | Supported |
|---------|-----------|
| 0.1.x   | Yes       |

## Reporting a vulnerability

Please open a private security advisory on GitHub or email the maintainer.

Do **not** open a public issue for security-sensitive reports.

## Cryptographic notes (v0.1)

- Ed25519 via PyNaCl
- Canonical JSON serialization for deterministic hashing
- Tenant public keys stored in-memory (replace with KMS / HSM in production)
