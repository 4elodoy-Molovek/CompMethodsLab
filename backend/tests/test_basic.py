import pytest
from core.models import BeetBatch, ExperimentConfig
from core.generators import MatrixGenerator
from core.losses import LossModel
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

def test_loss_formula():
    # calculated manually or simplified check
    # l = 1.1 + ...
    # Let params be 0
    # l = 1.1 + 0.1967 + 0.9989 * (I0 * 1.029^...)
    pass
