# QUANTAURA-Core

**Agent Execution Authorization Kernel** — the control plane that stops AI agents before they act.

> **Core invariant:** *No execution occurs without a verified, authorized intent.*

When an agent (or any caller) wants a side effect — transfer funds, write a database, call a tool — it must:

1. **Sign** a canonical payload (Ed25519)
2. **Submit** an intent to the kernel
3. Pass **policy evaluation**
4. Collect **multi-party / role approvals** when required
5. Advance a **linear state machine** to `AUTHORIZED`
6. Only then may the work run → `COMMITTED`

Audit trail is durable. Exports are CSV/JSON. Tenants are isolated.

This is the product wedge. Research modules (simulation, quant, cognitive scaffolds) ship alongside for teams building agentic research systems.

---

## Why this exists

Enterprises are deploying agents faster than they can govern them. Visibility is not enough — you need **authorization before execution**. QUANTAURA is that gate.

## Quick Start

```bash
git clone https://github.com/perseverancesworld-web/QUANTAURA-Core.git
cd QUANTAURA-Core
pip install -e ".[dev]"
quantaura-serve --reload
```

- API docs: http://localhost:8000/docs  
- Health: http://localhost:8000/health  

```bash
pytest -v
mkdocs serve
docker compose --profile dev up
```

## Protect any Python tool

```python
from quantaura.crypto.signatures import generate_keypair
from quantaura.sdk.python.client import IntentClient

priv, pub = generate_keypair()
client = IntentClient("http://localhost:8000", "agent-001", priv)

@client.protected_action("TRANSFER_FUNDS")
def transfer(amount: float, to: str):
    # Only runs if the kernel authorizes the intent
    return {"ok": True, "amount": amount, "to": to}

transfer(amount=50.0, to="alice")
```

## LangChain / LangGraph

```bash
pip install 'quantaura-core[langchain]'
```

```python
from quantaura.integrations.langchain_tools import protect_langchain_tool
# Wrap any LangChain tool or callable — invocations hit the kernel first
tool = protect_langchain_tool(my_tool, client=client, action_type="DATABASE_WRITE")
```

## Multi-tenant / hosted env

```bash
export QUANTAURA_ALLOWED_TENANTS=acme,beta
export QUANTAURA_REQUIRE_SIGNATURE=true
export QUANTAURA_DEFAULT_REQUIRED_APPROVALS=1
export QUANTAURA_ENV=production
quantaura-serve
```

## Audit export (compliance)

```bash
# JSON
curl -H "X-Tenant-ID: agent-001" "http://localhost:8000/v1/intents/audit"

# CSV download
curl -H "X-Tenant-ID: agent-001" "http://localhost:8000/v1/intents/audit?format=csv" -o audit.csv
```

## Architecture

```
Agent / LangChain tool
        |
        v
  Python SDK  -- signs payload -->  POST /v1/intents
                                        |
                    +-------------------+-------------------+
                    |  hash · verify · policy · approvals   |
                    |  state machine · durable ledger       |
                    +-------------------+-------------------+
                                        |
              AUTHORIZED --> execute --> COMMITTED
              PENDING --> human / multi-party gate
              REJECTED
```

## Modules

| Path | Role |
|------|------|
| `quantaura/crypto/` | Canonical JSON + Ed25519 |
| `quantaura/ledger/` | State machine + SQLite/Postgres + audit export |
| `quantaura/policy/` | Rules + roles + timeouts |
| `quantaura/api/` | FastAPI (`/v1/intents`, `/v1/research`) |
| `quantaura/sdk/` | `@protected_action` decorator |
| `quantaura/integrations/` | LangChain / LangGraph wrappers |
| `quantaura/core/` | Simulation, math, cognitive, quant (research OS) |

## Commercial

- **Open source (MIT):** self-host the full kernel  
- **Hosted / Pro:** multi-tenant control plane, audit retention, support  
- **Enterprise:** SSO, custom roles, SLA, on-prem  

See [docs/commercial.md](docs/commercial.md) and [site/index.md](site/index.md).

**Design partners:** if you run agents that touch money, data, or production systems and need a hard authorization gate, open an issue labeled `design-partner` or email joshua@perseverances.world.

## License

MIT
