# API

Base: `http://localhost:8000` · OpenAPI: `/docs`

## Authorization kernel

| Method | Path | Description |
|--------|------|-------------|
| POST | `/v1/intents` | Create intent |
| GET | `/v1/intents` | List for tenant |
| GET | `/v1/intents/{id}` | Get one |
| POST | `/v1/intents/{id}/approve` | Multi-party approve/reject |
| POST | `/v1/intents/{id}/transition` | State machine |
| POST | `/v1/intents/register-key` | Register Ed25519 public key |
| GET | `/v1/intents/audit?format=json\|csv` | Audit export |

## QPIE research

| Method | Path | Description |
|--------|------|-------------|
| GET | `/v1/qpie/benchmarks` | Known-solution + DEC suite |
| GET | `/v1/qpie/dec/status` | d²=0 residual |
| POST | `/v1/qpie/gauge/wilson` | Wilson action scan |
| POST | `/v1/qpie/schwinger/spectrum` | Exact diagonalization |
| POST | `/v1/qpie/vqe/stub` | Classical variational cross-check |
| GET | `/v1/qpie/topology/hopf_proxy` | Discrete Hopf proxy |
| POST | `/v1/qpie/discovery/score` | Experiment objective J |
| POST | `/v1/qpie/discovery/select` | Active selection |
| POST/GET | `/v1/qpie/hypotheses` | Hypothesis registry |
| POST/GET | `/v1/qpie/anomalies` | Anomaly registry |
| POST | `/v1/qpie/telemetry/manifest` | Experiment manifest |

## System

`GET /` · `GET /health` · `GET /system/status`
