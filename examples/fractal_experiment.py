"""Example: Basic fractal experiment demonstrating orchestration."""

import asyncio
import logging
from quantaura.orchestration.orchestrator import ResearchOrchestrator
from quantaura.orchestration.resource_manager import ResourceConfig
from quantaura.orchestration.retry_policy import RetryPolicy, RetryStrategy

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def mandelbrot_set(iterations: int = 100) -> dict:
    """Compute a small Mandelbrot set."""
    logger.info(f"Computing Mandelbrot set with {iterations} iterations")
    
    result = {"iterations": iterations, "points_computed": 1000 * iterations}
    logger.info(f"Mandelbrot complete: {result}")
    return result


def julia_set(c: complex = -0.7 + 0.27015j, iterations: int = 100) -> dict:
    """Compute a Julia set."""
    logger.info(f"Computing Julia set (c={c}) with {iterations} iterations")
    
    result = {"c": str(c), "iterations": iterations, "points_computed": 500 * iterations}
    logger.info(f"Julia complete: {result}")
    return result


def analyze_fractal_properties(mandelbrot_result: dict, julia_result: dict) -> dict:
    """Analyze combined fractal properties."""
    logger.info("Analyzing fractal properties...")
    
    result = {
        "mandelbrot_iterations": mandelbrot_result["iterations"],
        "julia_iterations": julia_result["iterations"],
        "total_points": (
            mandelbrot_result["points_computed"] + julia_result["points_computed"]
        ),
        "analysis": "Fractal dimension properties computed",
    }
    logger.info(f"Analysis complete: {result}")
    return result


async def main():
    """Run fractal experiment pipeline."""
    # Create orchestrator
    orchestrator = ResearchOrchestrator(max_concurrent=2)
    
    # Register Mandelbrot experiment
    mandelbrot_id = orchestrator.register_experiment(
        name="Mandelbrot Set",
        task=lambda: mandelbrot_set(iterations=200),
        priority=10,
        timeout_seconds=60,
        resource_config=ResourceConfig(max_memory_mb=512),
    )
    logger.info(f"Registered Mandelbrot: {mandelbrot_id}")
    
    # Register Julia experiment (independent)
    julia_id = orchestrator.register_experiment(
        name="Julia Set",
        task=lambda: julia_set(iterations=150),
        priority=10,
        timeout_seconds=60,
        resource_config=ResourceConfig(max_memory_mb=512),
    )
    logger.info(f"Registered Julia: {julia_id}")
    
    # Register analysis experiment (depends on both)
    analysis_id = orchestrator.register_experiment(
        name="Fractal Analysis",
        task=lambda: analyze_fractal_properties(
            mandelbrot_set(100), julia_set(iterations=100)
        ),
        dependencies=[mandelbrot_id, julia_id],
        priority=5,
        timeout_seconds=120,
    )
    logger.info(f"Registered Analysis: {analysis_id}")
    
    # Execute the experiment pipeline
    logger.info("Starting experiment execution...")
    result = await orchestrator.execute()
    
    # Print results
    logger.info("\n" + "="*60)
    logger.info("EXECUTION SUMMARY")
    logger.info("="*60)
    logger.info(f"Total experiments: {result['total_experiments']}")
    logger.info(f"Completed: {result['completed']}")
    logger.info(f"Failed: {result['failed']}")
    logger.info(f"Success rate: {result['success_rate']*100:.1f}%")
    logger.info("\nExperiment Details:")
    for name, details in result["experiments"].items():
        logger.info(f"  {name}:")
        logger.info(f"    State: {details['state']}")
        logger.info(f"    Duration: {(details.get('completed_at') or details.get('started_at', ''))[:19]}")
    
    logger.info("\nDashboard Data:")
    dash = result["dashboard_data"]
    logger.info(f"  Total Events: {dash['event_bus_stats']['total_events']}")
    logger.info(f"  Completed: {dash['experiments']['completed']}")
    logger.info(f"  Failed: {dash['experiments']['failed']}")
    logger.info(f"  Avg Duration: {dash['performance']['avg_duration_seconds']:.2f}s")


if __name__ == "__main__":
    asyncio.run(main())
