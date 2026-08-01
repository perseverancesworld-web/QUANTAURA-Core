# Integrations

## LangChain / LangGraph

```bash
pip install 'quantaura-core[langchain]'
```

```python
from quantaura.crypto.signatures import generate_keypair
from quantaura.sdk.python.client import IntentClient
from quantaura.integrations.langchain_tools import protect_langchain_tool

priv, _ = generate_keypair()
client = IntentClient("http://localhost:8000", "lc-agent", priv)

def write_row(msg: str) -> str:
    return f"wrote:{msg}"

gated = protect_langchain_tool(write_row, client=client, action_type="DATABASE_WRITE")
gated(msg="hello")
```

Every invocation submits a signed intent; the underlying function runs only if status is `AUTHORIZED`.

## REST

Any language can POST `/v1/intents` with `X-Tenant-ID` and optional `X-QUANTAURA-Signature`. See [API](api.md).
