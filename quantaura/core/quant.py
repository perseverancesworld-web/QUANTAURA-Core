"""Lightweight quantitative trading primitives."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence
import math


@dataclass
class Position:
    symbol: str
    quantity: float
    avg_price: float


@dataclass
class Portfolio:
    cash: float = 100_000.0
    positions: dict[str, Position] = field(default_factory=dict)

    def market_value(self, prices: dict[str, float]) -> float:
        equity = self.cash
        for sym, pos in self.positions.items():
            equity += pos.quantity * prices.get(sym, pos.avg_price)
        return equity

    def update(self, symbol: str, quantity: float, price: float) -> None:
        if symbol in self.positions:
            pos = self.positions[symbol]
            new_qty = pos.quantity + quantity
            if abs(new_qty) < 1e-12:
                del self.positions[symbol]
            else:
                pos.avg_price = (pos.avg_price * pos.quantity + price * quantity) / new_qty
                pos.quantity = new_qty
        else:
            self.positions[symbol] = Position(symbol, quantity, price)
        self.cash -= quantity * price


def simple_moving_average(series: Sequence[float], window: int) -> list[float]:
    if window <= 0:
        raise ValueError("window must be positive")
    out: list[float] = []
    for i in range(len(series)):
        start = max(0, i - window + 1)
        chunk = series[start : i + 1]
        out.append(sum(chunk) / len(chunk))
    return out


def returns(series: Sequence[float]) -> list[float]:
    if len(series) < 2:
        return []
    return [(series[i] / series[i - 1]) - 1.0 for i in range(1, len(series))]


def sharpe_ratio(rets: Sequence[float], risk_free: float = 0.0) -> float:
    if not rets:
        return 0.0
    mean = sum(rets) / len(rets)
    var = sum((r - mean) ** 2 for r in rets) / len(rets)
    std = math.sqrt(var)
    if std == 0:
        return 0.0
    return (mean - risk_free) / std


def momentum_signal(prices: Sequence[float], lookback: int = 20) -> float:
    if len(prices) <= lookback:
        return 0.0
    return (prices[-1] / prices[-1 - lookback]) - 1.0
