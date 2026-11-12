"""Tests for energy-accounted QPIE rhythmic dynamics."""

import numpy as np
import pytest

from quantaura.qpie.rhythm import simulate_rhythmic_network


def test_undamped_unforced_oscillator_conserves_energy():
    result = simulate_rhythmic_network(
        mass=np.array([1.0]),
        damping=np.array([0.0]),
        stiffness=np.array([4.0]),
        initial_position=np.array([1.0]),
        initial_velocity=np.array([0.0]),
        dt=0.002,
        steps=5000,
    )
    relative_drift = np.max(np.abs(result.energy - result.energy[0])) / result.energy[0]
    assert relative_drift < 1e-8
    assert result.max_abs_energy_balance_residual < 1e-8


def test_damped_system_loses_energy_without_drive():
    result = simulate_rhythmic_network(
        mass=np.array([1.0]),
        damping=np.array([0.2]),
        stiffness=np.array([4.0]),
        initial_position=np.array([1.0]),
        initial_velocity=np.array([0.0]),
        dt=0.002,
        steps=5000,
    )
    assert result.energy[-1] < result.energy[0]
    assert result.cumulative_dissipation[-1] > 0
    assert result.max_abs_energy_balance_residual < 2e-4


def test_driven_oscillator_energy_accounting():
    result = simulate_rhythmic_network(
        mass=np.array([1.0]),
        damping=np.array([0.15]),
        stiffness=np.array([4.0]),
        initial_position=np.array([0.0]),
        initial_velocity=np.array([0.0]),
        dt=0.001,
        steps=10000,
        drive=lambda t: np.array([np.sin(2.0 * t)]),
    )
    assert result.cumulative_input_work[-1] > 0
    assert result.cumulative_dissipation[-1] > 0
    assert result.max_abs_energy_balance_residual < 2e-4


def test_actuation_matrix_maps_drive_inputs():
    result = simulate_rhythmic_network(
        mass=np.array([1.0, 1.0]),
        damping=np.array([0.1, 0.1]),
        stiffness=np.diag([2.0, 3.0]),
        initial_position=np.zeros(2),
        initial_velocity=np.zeros(2),
        dt=0.01,
        steps=100,
        drive=lambda t: np.array([np.sin(t)]),
        actuation_matrix=np.array([[1.0], [0.5]]),
    )
    assert result.position.shape == (101, 2)
    assert np.linalg.norm(result.position[-1]) > 0


def test_nonlinear_cubic_restoring_force_is_supported():
    result = simulate_rhythmic_network(
        mass=np.array([1.0]),
        damping=np.array([0.05]),
        stiffness=np.array([1.0]),
        initial_position=np.array([0.5]),
        initial_velocity=np.array([0.0]),
        dt=0.002,
        steps=1000,
        cubic_stiffness=np.array([2.0]),
    )
    assert np.all(np.isfinite(result.energy))
    assert np.all(result.energy >= 0)


def test_invalid_negative_damping_is_rejected():
    with pytest.raises(ValueError):
        simulate_rhythmic_network(
            mass=np.array([1.0]),
            damping=np.array([-0.1]),
            stiffness=np.array([1.0]),
            initial_position=np.array([0.0]),
            initial_velocity=np.array([0.0]),
            dt=0.01,
            steps=10,
        )
