"""Example: Resonance simulation with orchestration and resource management."""

import asyncio
import logging
import math
from quantaura.orchestration.orchestrator import ResearchOrchestrator
from quantaura.orchestration.resource_manager import ResourceConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def initialize_resonance_field(frequency: float = 432.0) -> dict:
    """Initialize resonance field at specified frequency."""
    logger.info(f"Initializing resonance field at {frequency} Hz")
    return {
        "frequency": frequency,
        "harmonics": [frequency * i for i in range(1, 5)],
        "initial_energy": 100.0,
    }


def simulate_wave_propagation(field: dict, steps: int = 1000) -> dict:
    """Simulate wave propagation through the field."""
    logger.info(f"Simulating wave propagation for {steps} time steps")
    
    # Simulate energy distribution
    energy_levels = []
    for i in range(steps):
        # Simple harmonic motion simulation
        energy = field["initial_energy"] * math.cos(2 * math.pi * i / (steps / 10))
        energy_levels.append(max(0, energy))
    
    return {
        "frequency": field["frequency"],
        "steps": steps,
        "energy_levels": energy_levels,
        "average_energy": sum(energy_levels) / len(energy_levels),
        "peak_energy": max(energy_levels),
    }


def analyze_resonance_patterns(propagation: dict) -> dict:
    """Analyze patterns in resonance data."""
    logger.info(f"Analyzing resonance patterns at {propagation['frequency']} Hz")
    
    energies = propagation["energy_levels"]
    variance = sum((e - propagation["average_energy"])**2 for e in energies) / len(energies)
    
    return {
        "frequency": propagation["frequency"],
        "mean_energy": propagation["average_energy"],
        "peak_energy": propagation["peak_energy"],
        "variance": math.sqrt(variance),
        "stability": 1.0 - (math.sqrt(variance) / (propagation["average_energy"] + 0.001)),
    }


def compare_harmonics(primary: dict, secondary: dict) -> dict:
    """Compare primary and secondary harmonic resonances."""
    logger.info("Comparing harmonic resonances")
    
    return {
        "primary_frequency": primary["frequency"],
        "secondary_frequency": secondary["frequency"],
        "frequency_ratio": secondary["frequency"] / primary["frequency"],
        "energy_ratio": secondary["peak_energy"] / primary["peak_energy"],
        "phase_difference": abs(secondary["stability"] - primary["stability"]),
        "resonance_quality": min(primary["stability"], secondary["stability"]),
    }


def generate_report(comparison: dict) -> dict:
    """Generate final resonance analysis report."""
    logger.info("Generating resonance analysis report")
    
    return {
        "title": "Resonance Field Analysis",
        "frequency_ratio": f"{comparison['frequency_ratio']:.2f}",
        "resonance_quality": f"{comparison['resonance_quality']:.2%}",
        "recommendation": "High resonance quality - field is stable" 
                         if comparison["resonance_quality"] > 0.7 
                         else "Field requires optimization",
    }


async def main():
    """Run resonance simulation pipeline."""
    orchestrator = ResearchOrchestrator(max_concurrent=3)
    
    # Initialize primary field
    primary_init_id = orchestrator.register_experiment(
        name="Initialize Primary Field (432 Hz)",
        task=lambda: initialize_resonance_field(432.0),
        priority=20,
        resource_config=ResourceConfig(max_memory_mb=256),
    )
    
    # Initialize secondary field
    secondary_init_id = orchestrator.register_experiment(
        name="Initialize Secondary Field (528 Hz)",
        task=lambda: initialize_resonance_field(528.0),
        priority=20,
        resource_config=ResourceConfig(max_memory_mb=256),
    )
    
    # Simulate wave propagation (parallel)
    primary_prop_id = orchestrator.register_experiment(
        name="Primary Wave Propagation",
        task=lambda: simulate_wave_propagation(initialize_resonance_field(432.0), steps=2000),
        dependencies=[primary_init_id],
        priority=15,
        timeout_seconds=120,
        resource_config=ResourceConfig(max_memory_mb=1024),
    )
    
    secondary_prop_id = orchestrator.register_experiment(
        name="Secondary Wave Propagation",
        task=lambda: simulate_wave_propagation(initialize_resonance_field(528.0), steps=2000),
        dependencies=[secondary_init_id],
        priority=15,
        timeout_seconds=120,
        resource_config=ResourceConfig(max_memory_mb=1024),
    )
    
    # Analyze patterns (parallel)
    primary_analysis_id = orchestrator.register_experiment(
        name="Primary Pattern Analysis",
        task=lambda: analyze_resonance_patterns(simulate_wave_propagation(initialize_resonance_field(432.0))),
        dependencies=[primary_prop_id],
        priority=10,
    )
    
    secondary_analysis_id = orchestrator.register_experiment(
        name="Secondary Pattern Analysis",
        task=lambda: analyze_resonance_patterns(simulate_wave_propagation(initialize_resonance_field(528.0))),
        dependencies=[secondary_prop_id],
        priority=10,
    )
    
    # Compare harmonics
    comparison_id = orchestrator.register_experiment(
        name="Compare Harmonics",
        task=lambda: compare_harmonics(
            analyze_resonance_patterns(simulate_wave_propagation(initialize_resonance_field(432.0))),
            analyze_resonance_patterns(simulate_wave_propagation(initialize_resonance_field(528.0)))
        ),
        dependencies=[primary_analysis_id, secondary_analysis_id],
        priority=5,
    )
    
    # Generate report
    report_id = orchestrator.register_experiment(
        name="Generate Report",
        task=lambda: generate_report(
            compare_harmonics(
                analyze_resonance_patterns(simulate_wave_propagation(initialize_resonance_field(432.0))),
                analyze_resonance_patterns(simulate_wave_propagation(initialize_resonance_field(528.0)))
            )
        ),
        dependencies=[comparison_id],
        priority=1,
    )
    
    logger.info("Starting resonance simulation pipeline...")
    result = await orchestrator.execute()
    
    logger.info("\n" + "="*60)
    logger.info("RESONANCE SIMULATION SUMMARY")
    logger.info("="*60)
    logger.info(f"Total experiments: {result['total_experiments']}")
    logger.info(f"Completed: {result['completed']}")
    logger.info(f"Failed: {result['failed']}")
    logger.info(f"Success rate: {result['success_rate']*100:.1f}%")
    
    logger.info("\nSimulation Pipeline:")
    logger.info("  ├─ Initialize Primary & Secondary Fields (parallel)")
    logger.info("  ├─ Simulate Wave Propagation (parallel, depends on init)")
    logger.info("  ├─ Analyze Resonance Patterns (parallel, depends on propagation)")
    logger.info("  ├─ Compare Harmonics (depends on both analyses)")
    logger.info("  └─ Generate Report (depends on comparison)")
    
    logger.info("\nResource Utilization:")
    resources = result["dashboard_data"]["event_bus_stats"]
    logger.info(f"  Total events emitted: {resources['total_events']}")
    logger.info(f"  Event types tracked: {resources['unique_event_types']}")


if __name__ == "__main__":
    asyncio.run(main())
