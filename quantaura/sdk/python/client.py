"""Python SDK client — wraps agent tool calls behind intent authorization.

The decorator:
1. Captures call arguments as payload
2. Canonicalizes + signs with the tenant private key
3. Submits the intent to the kernel
4. Only executes the underlying function when AUTHORIZED
"""

from __future__ import annotations

import functools
from typing import Any, Callable

import httpx
from nacl.signing import SigningKey

from quantaura.crypto.signatures import canonicalize_payload


class IntentClient:
    def __init__(
        self,
        base_url: str,
        tenant_id: str,
        private_key_hex: str,
        timeout: float = 10.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.tenant_id = tenant_id
        self.signing_key = SigningKey(bytes.fromhex(private_key_hex))
        self.timeout = timeout

    def _sign(self, payload: dict) -> str:
        canonical = canonicalize_payload(payload)
        signed = self.signing_key.sign(canonical)
        return signed.signature.hex()

    def protected_action(self, action_type: str) -> Callable:
        """Decorator that forces every call through the authorization kernel."""

        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                payload = {"args": list(args), "kwargs": kwargs}
                signature = self._sign(payload)

                headers = {
                    "X-Tenant-ID": self.tenant_id,
                    "X-QUANTAURA-Signature": signature,
                }

                with httpx.Client(timeout=self.timeout) as client:
                    resp = client.post(
                        f"{self.base_url}/v1/intents",
                        json={"action_type": action_type, "payload": payload},
                        headers=headers,
                    )
                    resp.raise_for_status()
                    intent_data = resp.json()

                status = intent_data.get("status")
                if status == "REJECTED":
                    raise PermissionError(
                        f"Intent rejected by policy engine: {intent_data.get('reason')}"
                    )

                if status == "PENDING_AUTHORIZATION":
                    return {
                        "status": "PENDING_APPROVAL",
                        "intent_id": intent_data["intent_id"],
                        "reason": intent_data.get("reason"),
                    }

                result = func(*args, **kwargs)

                try:
                    with httpx.Client(timeout=self.timeout) as client:
                        client.post(
                            f"{self.base_url}/v1/intents/{intent_data['intent_id']}/transition",
                            json={"target_status": "COMMITTED"},
                            headers={"X-Tenant-ID": self.tenant_id},
                        )
                except Exception:
                    pass

                return result

            return wrapper

        return decorator
