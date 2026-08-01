# Changelog

## [0.2.0] — 2026-08-01

### Added
- Control-plane positioning (README, docs, landing `site/index.md`)
- LangChain / LangGraph integration (`quantaura.integrations.langchain_tools`)
- Audit export API: `GET /v1/intents/audit?format=json|csv`
- Multi-tenant env config (`QUANTAURA_ALLOWED_TENANTS`, `REQUIRE_SIGNATURE`, …)
- Commercial / design-partner docs
- Role field on approval requests

### Changed
- Package version 0.2.0; keywords emphasize agent authorization

## [0.1.0] — 2026-07-27

### Added
- Execution Authorization Kernel (Ed25519, policy, FSM, SQLite ledger)
- Multi-party approvals, research modules, Docker, MkDocs, CI
