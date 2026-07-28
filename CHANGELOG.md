# Changelog

## [0.1.0] — 2026-07-27

### Added
- Execution Authorization Kernel (Ed25519, policy engine, linear state machine)
- Durable SQLite ledger with audit log; process-local paths; shared in-memory mode
- Multi-party approvals with optional roles and timeouts
- FastAPI surface: `/v1/intents`, `/v1/research`
- Python SDK `@protected_action` decorator
- Core research modules: simulation, math/entropy, cognitive architecture, quant
- Experiment configs + nested simulation runner
- Mock / CSV price data connectors
- Docker multi-stage + compose profiles (incl. Postgres)
- MkDocs documentation
- GitHub Actions CI (pytest)

### Fixed
- Canonical JSON test assertion
- SQLite `:memory:` connection isolation
