# QUANTAURA

## Stop agents before they act.

**Execution Authorization Kernel** for AI agents.

No transfer, no write, no tool call — until the intent is signed, policy-checked, and authorized.

### The invariant

> No execution occurs without a verified, authorized intent.

### 60-second install

```bash
pip install quantaura-core
quantaura-serve --reload
```

Wrap any tool:

```python
@client.protected_action("TRANSFER_FUNDS")
def transfer(amount, to): ...
```

### Who it's for

- Teams shipping **LangChain / LangGraph / custom agents** into production  
- Security & platform eng who need **audit + multi-party approval** before side effects  
- Builders who refuse “hope the prompt behaves”

### Open source + commercial

| | Self-host | Pro (hosted) | Enterprise |
|--|-----------|--------------|------------|
| Kernel | ✓ MIT | ✓ | ✓ |
| Audit export | ✓ | ✓ retained | ✓ + SIEM |
| Multi-tenant | env flags | managed | SSO / RBAC |
| Support | community | email | SLA |

### Design partners

We’re onboarding a small set of teams. Bring one real agent tool you cannot afford to run ungoverned.

→ [GitHub](https://github.com/perseverancesworld-web/QUANTAURA-Core) · [Docs](https://github.com/perseverancesworld-web/QUANTAURA-Core/tree/main/docs) · joshua@perseverances.world
