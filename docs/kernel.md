# Execution Authorization Kernel (v0.1)

## Invariant

**No execution occurs without a verified, authorized intent.**

## Intent lifecycle

```
DRAFT
  |
  +-> PENDING_AUTHORIZATION --> AUTHORIZED --> COMMITTED --> COMPENSATED
  |         |                       |
  |         +-----------------------+--> REJECTED
  |
  +-> REJECTED
```

## Cryptography

- Canonical JSON (sorted keys, no whitespace)
- SHA-256 hash
- Ed25519 signatures (PyNaCl)

## Multi-party approvals

POST `/v1/intents/{id}/approve` with header `X-Actor`.
Requires N distinct approvers when `required_approvals > 1`.

## SDK

```python
from quantaura.sdk.python.client import IntentClient
from quantaura.crypto.signatures import generate_keypair

priv, pub = generate_keypair()
client = IntentClient("http://localhost:8000", "my-tenant", priv)

@client.protected_action("TRANSFER_FUNDS")
def move_money(amount: float, to: str):
    ...
```
