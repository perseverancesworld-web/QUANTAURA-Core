# QUANTAURA-Core

**Unified research operating system + Execution Authorization Kernel**

Integrating cognitive architectures, simulations, mathematical models, quantitative trading, and a cryptographic intent-authorization loop.

> **Core Invariant:** *No execution occurs without a verified, authorized intent.*

## Scientific Status

| Component                    | Status             |
|------------------------------|--------------------|
| Architecture                 | Prototype          |
| Execution Kernel (v0.1)      | Active             |
| Durable ledger (SQLite)      | Active             |
| Multi-party approvals        | Active             |
| Simulation engine            | Active             |
| Math / entropy models        | Active             |
| Cognitive architecture       | Scaffold           |
| Quant primitives             | Scaffold           |
| Visualization                | Alpha              |
| AI orchestration             | Experimental       |

## What is the Execution Authorization Kernel?

When an AI agent (or any caller) wants to perform a side-effecting action it must:

1. **Sign** a canonical payload (Ed25519)
2. **Submit** an *intent* to the kernel
3. Pass **policy evaluation** (thresholds, human-in-the-loop rules)
4. Collect **multi-party approvals** when required
5. Advance through a **linear state machine** (`DRAFT → … → AUTHORIZED → COMMITTED`)
6. Only then may the underlying work execute

This guarantees auditability, non-repudiation, and policy enforcement before any real-world effect.

## Quick Start

```bash
git clone https://github.com/perseverancesworld-web/QUANTAURA-Core.git
cd QUANTAURA-Core

pip install -e ".[dev]"
quantaura-serve --reload
```

Open http://localhost:8000 and http://localhost:8000/docs

### Tests

```bash
pytest -v
```

### Docs

```bash
mkdocs serve
```

### Docker

```bash
# Development (hot-reload + volume mount)
docker compose --profile dev up

# Production
docker compose --profile prod up
```

## Kernel Modules (v0.1)

| Path | Responsibility |
|------|----------------|
| `quantaura/crypto/` | Canonical JSON + Ed25519 sign/verify |
| `quantaura/ledger/` | Linear state machine + durable SQLite store + audit log |
| `quantaura/policy/` | Deterministic policy engine + multi-party approvals |
| `quantaura/api/` | FastAPI surface (`/v1/intents`) |
| `quantaura/sdk/python/` | Client decorator that forces every tool call through the kernel |
| `quantaura/core/` | Simulation, math models, cognitive architecture, quant primitives |

## Example — Protecting an Agent Tool

```python
from quantaura.crypto.signatures import generate_keypair
from quantaura.sdk.python.client import IntentClient

private_hex, public_hex = generate_keypair()

client = IntentClient(
    base_url="http://localhost:8000",
    tenant_id="agent-001",
    private_key_hex=private_hex,
)

@client.protected_action("TRANSFER_FUNDS")
def transfer(amount: float, to: str):
    print(f"Actually moving ${amount} to {to}")
    return {"ok": True}

result = transfer(amount=50.0, to="alice")
```

## Architecture Overview

```
Agent / Tool Call
       |
       v
+------------------+
|  Python SDK      |  <- signs payload
+--------+---------+
         | POST /v1/intents
         v
+------------------+
|  Intent API      |
|  - hash          |
|  - verify sig    |
|  - policy eval   |
|  - multi-party   |
|  - state machine |
|  - durable store |
+--------+---------+
         |
    AUTHORIZED --> execute real work --> COMMITTED
         |
 PENDING_AUTHORIZATION --> human / multi-party gate
         |
    REJECTED
```

## Core Research Modules

- **Simulation** — discrete-time nested engines (growth, market regimes)
- **Math models** — Shannon entropy, KL divergence, box-counting fractal dimension
- **Cognitive architecture** — fractal tree of perception → deliberation → action nodes
- **Quant** — portfolio, SMA, Sharpe, momentum signals

## Roadmap

- Postgres / event-store ledger backend
- Richer multi-party workflows (roles, timeouts, escalation)
- Deeper cognitive nesting & AGI research loops
- Live data connectors & execution venues
- Visualization surface

See `docs/` for deeper guides.

## License

MIT
