"""Price data connector stubs — mock + CSV for offline research."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Optional
import csv
import math
import random
import time


@dataclass
class PriceBar:
    symbol: str
    ts: float
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0


class MockPriceFeed:
    """Synthetic geometric Brownian motion feed for demos/tests."""

    def __init__(
        self,
        symbol: str = "MOCK",
        start_price: float = 100.0,
        drift: float = 0.0001,
        vol: float = 0.01,
        seed: Optional[int] = None,
    ) -> None:
        self.symbol = symbol
        self.price = start_price
        self.drift = drift
        self.vol = vol
        self._rng = random.Random(seed)

    def next_bar(self) -> PriceBar:
        shock = self._rng.gauss(0, self.vol)
        new_close = self.price * math.exp(self.drift + shock)
        high = max(self.price, new_close) * (1 + abs(self._rng.gauss(0, self.vol / 2)))
        low = min(self.price, new_close) * (1 - abs(self._rng.gauss(0, self.vol / 2)))
        bar = PriceBar(
            symbol=self.symbol,
            ts=time.time(),
            open=self.price,
            high=high,
            low=low,
            close=new_close,
            volume=float(self._rng.randint(1000, 50000)),
        )
        self.price = new_close
        return bar

    def stream(self, n: int) -> Iterator[PriceBar]:
        for _ in range(n):
            yield self.next_bar()


class CSVPriceFeed:
    """Load OHLCV bars from a simple CSV (symbol,ts,open,high,low,close,volume)."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def bars(self) -> list[PriceBar]:
        out: list[PriceBar] = []
        with self.path.open() as f:
            reader = csv.DictReader(f)
            for row in reader:
                out.append(
                    PriceBar(
                        symbol=row.get("symbol", "UNK"),
                        ts=float(row.get("ts", 0)),
                        open=float(row["open"]),
                        high=float(row["high"]),
                        low=float(row["low"]),
                        close=float(row["close"]),
                        volume=float(row.get("volume", 0)),
                    )
                )
        return out
