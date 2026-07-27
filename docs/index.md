# QUANTAURA-Core

Unified research operating system integrating cognitive architectures, simulations, mathematical models, quantitative trading, **and a cryptographic Execution Authorization Kernel**.

## Core Invariant

> **No execution occurs without a verified, authorized intent.**

## Modules

- **Crypto** — canonical JSON + Ed25519
- **Ledger** — intent state machine + durable SQLite store
- **Policy** — deterministic guardrails + multi-party approvals
- **API** — `/v1/intents`
- **SDK** — Python decorator that forces tool calls through the kernel
- **Core** — simulation, math, cognitive architecture, quant

See the [Quickstart](quickstart.md) to get running in under a minute.
