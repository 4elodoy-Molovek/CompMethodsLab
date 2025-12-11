import pytest
from core.models import BeetBatch, ExperimentConfig
from core.generators import MatrixGenerator
from core.losses import LossModel
from algorithms.optimizer import Optimizer
import numpy as np

def test_degradation_uniform():
    config = ExperimentConfig(
        n=3, m=100, a_min=10, a_max=12,
        beta1=0.9, beta2=0.95, distribution_type='uniform'
    )
    batches = [
        BeetBatch(0, 10, 5, 0.5, 2, 0.63),
        BeetBatch(1, 11, 5, 0.5, 2, 0.63),
        BeetBatch(2, 12, 5, 0.5, 2, 0.63)
    ]
    
    B = MatrixGenerator.generate_coefficients(config, batches)
    assert B.shape == (3, 3)
    # Check bounds (skipping column 0)
    assert np.all(B[:, 1:] >= 0.9)
    assert np.all(B[:, 1:] <= 0.95)

def test_states_logic():
    # Setup case with n=2 to test transition to 2nd stage
    batches = [
        BeetBatch(0, 100, 0,0,0,0),
        BeetBatch(1, 100, 0,0,0,0)
    ]
    # n=2, so B is 2x2
    B = np.zeros((2, 2))
    # Transition to stage 1 (index 1) uses B[:, 1]
    B[0, 1] = 0.9
    
    C = MatrixGenerator.generate_states(batches, B)
    # C[0,0] = 100
    # C[0,1] = C[0,0] * B[0,1] = 100 * 0.9 = 90
    assert C[0, 0] == 100
    assert abs(C[0, 1] - 90.0) < 1e-6 

def test_loss_formula_with_division():
    """Test that losses are divided by 100 before subtracting from C."""
    batches = [
        BeetBatch(0, 100, 5, 0.5, 2, 0.63)
    ]
    
    # Calculate losses
    L = LossModel.calculate_losses(batches, num_stages=2)
    
    # Create simple C matrix
    C = np.array([[100.0, 90.0]])
    
    # Calculate final yield matrix
    S_tilde = LossModel.calculate_final_yield_matrix(C, L)
    
    # Verify that S_tilde = C - L/100
    expected = C - L / 100.0
    assert np.allclose(S_tilde, expected)
    
    # Verify that loss is actually divided (not just subtracted)
    # If L[0,0] = 5.0, then S_tilde[0,0] should be 100 - 5.0/100 = 99.95, not 95.0
    assert S_tilde[0, 0] > C[0, 0] - L[0, 0]  # Should be less loss due to division

def test_final_mass_calculation():
    """Test calculation of final product mass: S = S(σ) × M × d."""
    yield_value = 10.5
    mass_per_batch = 1000.0
    days_per_stage = 7
    
    final_mass = Optimizer.calculate_final_mass(yield_value, mass_per_batch, days_per_stage)
    
    expected = yield_value * mass_per_batch * days_per_stage
    assert abs(final_mass - expected) < 1e-6
    assert final_mass == 73500.0  # 10.5 * 1000 * 7

def test_ripening_logic():
    """Test that ripening stages have coefficients > 1, wilting stages < 1."""
    config = ExperimentConfig(
        n=5, m=100, a_min=10, a_max=12,
        beta1=0.9, beta2=0.95, distribution_type='uniform',
        enable_ripening=True, v=2, beta_max=1.05
    )
    batches = [
        BeetBatch(0, 10, 5, 0.5, 2, 0.63),
        BeetBatch(1, 11, 5, 0.5, 2, 0.63),
        BeetBatch(2, 12, 5, 0.5, 2, 0.63),
        BeetBatch(3, 13, 5, 0.5, 2, 0.63),
        BeetBatch(4, 14, 5, 0.5, 2, 0.63)
    ]
    
    B = MatrixGenerator.generate_coefficients(config, batches)
    
    # Stage 1 (j=1) should be ripening: b > 1
    assert np.all(B[:, 1] > 1.0)
    assert np.all(B[:, 1] <= 1.05)
    
    # Stages 2-4 (j=2,3,4) should be wilting: b < 1
    assert np.all(B[:, 2:] < 1.0)
    assert np.all(B[:, 2:] >= 0.9)
    assert np.all(B[:, 2:] <= 0.95)

def test_ripening_auto_beta_max():
    """Test automatic calculation of beta_max when not provided."""
    config = ExperimentConfig(
        n=5, m=100, a_min=10, a_max=12,
        beta1=0.9, beta2=0.95, distribution_type='uniform',
        enable_ripening=True, v=2, beta_max=None
    )
    batches = [
        BeetBatch(0, 10, 5, 0.5, 2, 0.63),
        BeetBatch(1, 11, 5, 0.5, 2, 0.63),
        BeetBatch(2, 12, 5, 0.5, 2, 0.63),
        BeetBatch(3, 13, 5, 0.5, 2, 0.63),
        BeetBatch(4, 14, 5, 0.5, 2, 0.63)
    ]
    
    B = MatrixGenerator.generate_coefficients(config, batches)
    
    # beta_max should be auto-calculated as (n-1)/(n-2) = 4/3 = 1.333...
    # So ripening coefficients should be <= 1.333...
    assert np.all(B[:, 1] <= 1.34)  # Allow small tolerance

def test_concentrated_ripening():
    """Test concentrated distribution for ripening stages."""
    config = ExperimentConfig(
        n=5, m=100, a_min=10, a_max=12,
        beta1=0.9, beta2=0.95, distribution_type='concentrated',
        enable_ripening=True, v=2, beta_max=1.1
    )
    
    # Generate batches with concentrated distribution params
    batches = []
    for i in range(5):
        batch = BeetBatch(
            i, 10 + i, 5, 0.5, 2, 0.63,
            delta=0.01, beta_range_start=0.91, beta_range_end=0.93,
            delta_ripening=0.02, beta_range_start_ripening=1.05, beta_range_end_ripening=1.09
        )
        batches.append(batch)
    
    B = MatrixGenerator.generate_coefficients(config, batches)
    
    # Ripening stage (j=1) should use concentrated range
    assert np.all(B[:, 1] >= 1.05)
    assert np.all(B[:, 1] <= 1.09)
    
    # Wilting stages should use concentrated range for wilting
    assert np.all(B[:, 2:] >= 0.91)
    assert np.all(B[:, 2:] <= 0.93)
