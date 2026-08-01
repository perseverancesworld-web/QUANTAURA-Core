# API

Base URL: `http://localhost:8000`

## Intents

| Method | Path | Description |
|--------|------|-------------|
| POST | `/v1/intents` | Create intent (headers: `X-Tenant-ID`, optional signature) |
| GET | `/v1/intents` | List intents for tenant |
| GET | `/v1/intents/{id}` | Get one intent |
| POST | `/v1/intents/{id}/approve` | Multi-party approve/reject (`X-Actor`, optional `role`) |
| POST | `/v1/intents/{id}/transition` | Advance state machine |
| POST | `/v1/intents/register-key` | Register Ed25519 public key for tenant |
| GET | `/v1/intents/audit?format=json\|csv` | **Audit export** for tenant |

## System

| Method | Path |
|--------|------|
| GET | `/` |
| GET | `/health` |
| GET | `/system/status` |

## Research

See OpenAPI at `/docs` for `/v1/research/*` simulation and math endpoints.
