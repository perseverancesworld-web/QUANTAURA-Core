# API Reference

Base URL: `http://localhost:8000`

Interactive docs: `/docs`

## System

- `GET /` — service info
- `GET /health` — health check
- `GET /system/status` — component status

## Intents

- `POST /v1/intents` — create intent (headers: `X-Tenant-ID`, optional `X-QUANTAURA-Signature`)
- `GET /v1/intents/{id}` — get intent
- `GET /v1/intents` — list for tenant
- `POST /v1/intents/{id}/transition` — advance state machine
- `POST /v1/intents/{id}/approve` — multi-party approval (headers: `X-Tenant-ID`, `X-Actor`)
- `POST /v1/intents/register-key` — register tenant public key
