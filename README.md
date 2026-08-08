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

This is the **product wedge**. Alongside it ships **QPIE** (Physical Intelligence Engine) — a computational laboratory for coupled physical systems — plus simulation, quant, and cognitive scaffolds.

**Current package version:** `0.4.0`

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

## QPIE — Physical Intelligence Engine

Research stack for **state-spaces of coupled physical systems** (not “optimize one material”):

- Common geometry / **DEC** incidence complex with \(d^2 = 0\)
- **U(1) lattice gauge** (plaquettes, Wilson action)
- Topology proxies (Hopf / skyrmion), vortex **helicity**
- Causal graph with `do(X=x)` interventions
- Transition certificates + **known-physics firewall** (Tier 0–5; no auto Tier-5 claims)
- Schwinger-like **exact diagonalization** lab (small systems)
- Hypothesis registry, anomalies, active experiment selection
- Telemetry manifests (sim ↔ measure pairing)

```bash
curl localhost:8000/v1/qpie/benchmarks
curl localhost:8000/v1/qpie/dec/status
curl -X POST localhost:8000/v1/qpie/schwinger/spectrum \
  -H 'content-type: application/json' -d '{"n_sites":3}'
```

```python
from quantaura.qpie import run_all_benchmarks, LatticeGaugeU1
from quantaura.qpie.dec import GridComplex2D

print(run_all_benchmarks())
print(LatticeGaugeU1.zeros(8, 8).wilson_action())  # 0.0
c = GridComplex2D(6, 6)
assert (c.incidence_d1() @ c.incidence_d0()).max() == 0
```

Docs: [docs/qpie.md](docs/qpie.md)

QPIE **proposes** experiments; the **Execution Authorization Kernel** still decides whether anything physical or privileged may run.

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

Research / discovery (no side effects required):
  POST/GET /v1/qpie/*   DEC · gauge · Schwinger · topology · hypotheses
```

## Modules

| Path | Role |
|------|------|
| `quantaura/crypto/` | Canonical JSON + Ed25519 |
| `quantaura/ledger/` | State machine + SQLite/Postgres + audit export |
| `quantaura/policy/` | Rules + roles + timeouts |
| `quantaura/api/` | FastAPI (`/v1/intents`, `/v1/research`, `/v1/qpie`) |
| `quantaura/sdk/` | `@protected_action` decorator |
| `quantaura/integrations/` | LangChain / LangGraph wrappers |
| `quantaura/qpie/` | Physical Intelligence Engine (DEC, gauge, Schwinger, firewall, …) |
| `quantaura/core/` | Simulation, math, cognitive, quant scaffolds |

## Commercial

- **Open source (MIT):** self-host the full kernel + QPIE  
- **Hosted / Pro:** multi-tenant control plane, audit retention, support  
- **Enterprise:** SSO, custom roles, SLA, on-prem  

See [docs/commercial.md](docs/commercial.md) and [site/index.md](site/index.md).

**Design partners:** if you run agents that touch money, data, or production systems and need a hard authorization gate, open an issue labeled `design-partner` or email joshua@perseverances.world.

## License

MIT
