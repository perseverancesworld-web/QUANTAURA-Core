# Architecture

```
Agent / Tool Call
       |
       v
 Python SDK  -->  signs payload
       |
       v
 Intent API
  - hash + verify signature
  - policy evaluation
  - multi-party approvals
  - state machine
  - durable SQLite ledger + audit log
       |
  AUTHORIZED --> execute --> COMMITTED
  PENDING --> human gate
  REJECTED
```

## Packages

| Package | Role |
|---------|------|
| quantaura.crypto | Canonical JSON + Ed25519 |
| quantaura.ledger | State machine + SQLite store |
| quantaura.policy | Rules + multi-party approvals |
| quantaura.api | FastAPI surface |
| quantaura.sdk | Client libraries |
| quantaura.core | Simulation, math, cognitive, quant |
