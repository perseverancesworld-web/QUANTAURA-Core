"""Example: Quantitative trading pipeline with orchestration."""

import asyncio
import logging
from quantaura.orchestration.orchestrator import ResearchOrchestrator
from quantaura.orchestration.resource_manager import ResourceConfig
from quantaura.orchestration.retry_policy import RetryPolicy, RetryStrategy

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def fetch_market_data(symbol: str = "AAPL") -> dict:
    """Fetch historical market data."""
    logger.info(f"Fetching market data for {symbol}")
    # Simulate data fetch
    return {
        "symbol": symbol,
        "data_points": 1000,
        "price_range": (100.0, 150.0),
    }


def compute_technical_indicators(market_data: dict) -> dict:
    """Compute technical indicators (MA, RSI, MACD)."""
    logger.info(f"Computing indicators for {market_data['symbol']}")
    return {
        "symbol": market_data["symbol"],
        "sma_20": 125.5,
        "sma_50": 122.3,
        "rsi_14": 65.2,
        "macd": 2.1,
    }


def generate_signals(indicators: dict) -> dict:
    """Generate buy/sell signals based on indicators."""
    logger.info(f"Generating trading signals for {indicators['symbol']}")
    return {
        "symbol": indicators["symbol"],
        "signal": "BUY" if indicators["rsi_14"] > 50 else "SELL",
        "confidence": 0.75,
        "indicators": indicators,
    }


def backtest_strategy(signals: dict) -> dict:
    """Backtest trading strategy on historical data."""
    logger.info(f"Backtesting strategy for {signals['symbol']}")
    return {
        "symbol": signals["symbol"],
        "total_return": 18.5,
        "sharpe_ratio": 1.23,
        "max_drawdown": -12.3,
        "trades": 42,
        "win_rate": 0.64,
    }


def optimize_parameters() -> dict:
    """Optimize strategy parameters."""
    logger.info("Optimizing strategy parameters")
    return {
        "optimal_sma_fast": 18,
        "optimal_sma_slow": 48,
        "optimal_rsi_threshold": 52,
    }


def validate_results(backtest: dict, params: dict) -> dict:
    """Validate and summarize results."""
    logger.info("Validating trading strategy results")
    return {
        "strategy_valid": True,
        "recommended": backtest["sharpe_ratio"] > 1.0,
        "summary": f"Strategy returned {backtest['total_return']:.1f}% with Sharpe {backtest['sharpe_ratio']:.2f}",
        "next_steps": "Deploy to paper trading" if backtest["sharpe_ratio"] > 1.0 else "Revisit parameters",
    }


async def main():
    """Run quantitative trading pipeline."""
    orchestrator = ResearchOrchestrator(max_concurrent=3)
    
    # Parallel data fetching for multiple symbols
    aapl_data_id = orchestrator.register_experiment(
        name="Fetch AAPL Data",
        task=lambda: fetch_market_data("AAPL"),
        priority=20,
        resource_config=ResourceConfig(max_memory_mb=1024),
    )
    
    msft_data_id = orchestrator.register_experiment(
        name="Fetch MSFT Data",
        task=lambda: fetch_market_data("MSFT"),
        priority=20,
        resource_config=ResourceConfig(max_memory_mb=1024),
    )
    
    # Compute indicators (depends on data fetches)
    aapl_indicators_id = orchestrator.register_experiment(
        name="AAPL Indicators",
        task=lambda: compute_technical_indicators(fetch_market_data("AAPL")),
        dependencies=[aapl_data_id],
        priority=15,
    )
    
    msft_indicators_id = orchestrator.register_experiment(
        name="MSFT Indicators",
        task=lambda: compute_technical_indicators(fetch_market_data("MSFT")),
        dependencies=[msft_data_id],
        priority=15,
    )
    
    # Generate signals
    aapl_signals_id = orchestrator.register_experiment(
        name="AAPL Signals",
        task=lambda: generate_signals(compute_technical_indicators(fetch_market_data("AAPL"))),
        dependencies=[aapl_indicators_id],
        priority=10,
    )
    
    # Backtest
    backtest_id = orchestrator.register_experiment(
        name="Backtest Strategy",
        task=lambda: backtest_strategy(generate_signals(compute_technical_indicators(fetch_market_data("AAPL")))),
        dependencies=[aapl_signals_id],
        priority=5,
    )
    
    # Optimize (independent)
    optimize_id = orchestrator.register_experiment(
        name="Optimize Parameters",
        task=optimize_parameters,
        priority=8,
    )
    
    # Validation (depends on backtest and optimize)
    validate_id = orchestrator.register_experiment(
        name="Validate Results",
        task=lambda: validate_results(
            backtest_strategy(generate_signals(compute_technical_indicators(fetch_market_data("AAPL")))),
            optimize_parameters()
        ),
        dependencies=[backtest_id, optimize_id],
        priority=1,
        retry_policy=RetryPolicy(max_retries=2),
    )
    
    logger.info("Starting quantitative trading pipeline...")
    result = await orchestrator.execute()
    
    logger.info("\n" + "="*60)
    logger.info("TRADING PIPELINE SUMMARY")
    logger.info("="*60)
    logger.info(f"Total experiments: {result['total_experiments']}")
    logger.info(f"Completed: {result['completed']}")
    logger.info(f"Failed: {result['failed']}")
    logger.info(f"Success rate: {result['success_rate']*100:.1f}%")
    
    logger.info("\nPipeline Execution Flow:")
    logger.info("  1. Fetch market data (parallel: AAPL, MSFT)")
    logger.info("  2. Compute technical indicators (depends on fetches)")
    logger.info("  3. Generate trading signals (depends on indicators)")
    logger.info("  4. Backtest strategy (depends on signals)")
    logger.info("  5. Optimize parameters (independent)")
    logger.info("  6. Validate results (depends on backtest + optimize)")


if __name__ == "__main__":
    asyncio.run(main())
