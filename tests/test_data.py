from quantaura.data.connectors import MockPriceFeed


def test_mock_feed():
    feed = MockPriceFeed(symbol="TEST", start_price=100.0, seed=42)
    bars = list(feed.stream(5))
    assert len(bars) == 5
    assert bars[0].symbol == "TEST"
    assert bars[-1].close != 100.0
