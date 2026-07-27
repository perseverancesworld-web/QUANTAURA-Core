#!/usr/bin/env python3
"""End-to-end demo of the Execution Authorization Kernel.

Run with the API server already up:
    quantaura-serve --reload
    python examples/demo_kernel.py
"""

from quantaura.crypto.signatures import generate_keypair
from quantaura.sdk.python.client import IntentClient
from quantaura.core.simulation import SimulationEngine, simple_growth_step
from quantaura.core.cognitive import build_default_architecture
from quantaura.core.quant import Portfolio, momentum_signal
import httpx

BASE = "http://localhost:8000"


def main() -> None:
    print("=== QUANTAURA-Core v0.1 Demo ===\n")

    r = httpx.get(f"{BASE}/health")
    print(f"1. Health: {r.json()}")

    priv, pub = generate_keypair()
    httpx.post(
        f"{BASE}/v1/intents/register-key",
        params={"public_key_hex": pub},
        headers={"X-Tenant-ID": "demo-agent"},
    )
    print("2. Registered tenant key")

    client = IntentClient(BASE, "demo-agent", priv)

    @client.protected_action("DATABASE_WRITE")
    def write_row(table: str, data: dict):
        return {"written": True, "table": table, "data": data}

    result = write_row(table="events", data={"event": "boot"})
    print(f"3. Auto-authorized write: {result}")

    @client.protected_action("TRANSFER_FUNDS")
    def transfer(amount: float, to: str):
        return {"transferred": amount, "to": to}

    pending = transfer(amount=50.0, to="alice")
    print(f"4. Transfer (pending approval): {pending}")

    if isinstance(pending, dict) and pending.get("status") == "PENDING_APPROVAL":
        intent_id = pending["intent_id"]
        approved = httpx.post(
            f"{BASE}/v1/intents/{intent_id}/approve",
            json={"decision": "approve", "comment": "demo approval"},
            headers={"X-Tenant-ID": "demo-agent", "X-Actor": "human-ops"},
        )
        print(f"5. After human approval: {approved.json()['status']}")

    eng = SimulationEngine("growth")
    sim = eng.run({"population": 100.0, "growth_rate": 0.08}, simple_growth_step, n_steps=5)
    print(f"6. Simulation final population: {sim.final_state['population']:.2f}")

    arch = build_default_architecture()
    print(f"7. Cognitive architecture nodes: {arch.summary()['node_count']}")

    port = Portfolio(cash=50_000)
    port.update("AAPL", 20, 150.0)
    print(f"8. Portfolio MV @ 160: {port.market_value({'AAPL': 160.0}):.2f}")

    prices = [100, 102, 101, 105, 110, 108, 112, 115]
    print(f"9. Momentum signal: {momentum_signal(prices, lookback=4):.4f}")

    print("\n=== Demo complete ===")


if __name__ == "__main__":
    main()
