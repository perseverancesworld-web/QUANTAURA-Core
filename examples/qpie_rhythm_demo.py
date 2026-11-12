"""Two-degree-of-freedom rhythmic network demo for QPIE.

Run with: python examples/qpie_rhythm_demo.py
"""

import numpy as np

from quantaura.qpie.rhythm import simulate_rhythmic_network


def main() -> None:
    # Two masses coupled by a spring. The matrix is the mechanical graph's
    # stiffness representation; the graph itself remains a separate object.
    mass = np.array([1.0, 1.0])
    damping = np.array([[0.08, 0.0], [0.0, 0.08]])
    stiffness = np.array([[3.0, -1.0], [-1.0, 3.0]])
    actuation = np.array([[1.0], [0.0]])

    result = simulate_rhythmic_network(
        mass=mass,
        damping=damping,
        stiffness=stiffness,
        initial_position=np.zeros(2),
        initial_velocity=np.zeros(2),
        dt=0.002,
        steps=10000,
        drive=lambda t: np.array([np.sin(np.sqrt(2.0) * t)]),
        actuation_matrix=actuation,
    )

    print("Final displacement:", result.position[-1])
    print("Stored energy:", result.energy[-1])
    print("Input work:", result.cumulative_input_work[-1])
    print("Dissipated energy:", result.cumulative_dissipation[-1])
    print("Maximum energy-balance residual:", result.max_abs_energy_balance_residual)


if __name__ == "__main__":
    main()
