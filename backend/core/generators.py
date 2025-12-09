import numpy as np
from typing import List, Tuple
from .models import BeetBatch, ExperimentConfig

class MatrixGenerator:
    @staticmethod
    def generate_coefficients(config: ExperimentConfig, batches: List[BeetBatch]) -> np.ndarray:
        """
        Generates the matrix B of degradation coefficients b_{ij}.
        Size: n x (n-1) because j goes from 2 to n (columns 1 to n-1 in 0-indexed matrix).
        Actually, let's make it n x n and keep column 0 empty or 1.0 for convenience.
        Task says b_{i,j-1} = c_{ij} / c_{i,j-1} for j=2..n.
        So we have n columns corresponding to transitions.
        Let's store b_{ij} where j is the stage index (0-indexed).
        Stage 0 is initial state.
        Coef for stage 0->1 is at index 0?
        Task: b_{i,j-1} for j=2..n. So indices 1..n-1?
        Let's produce an n x n matrix where B[i, j] is the coefficient for transition to stage j.
        B[i, 0] is irrelevant (or 1.0).
        B[i, j] is coef to get from stage j-1 to j.
        """
        n = config.n
        B = np.zeros((n, n))
        
        # Determine ripening stages
        v = config.v if config.enable_ripening and config.v else 0
        
        # Auto-calculate beta_max if not provided (recommended formula from task.md)
        beta_max = config.beta_max
        if config.enable_ripening and beta_max is None:
            if n > 2:
                beta_max = (n - 1) / (n - 2)
            else:
                beta_max = 1.1  # fallback for small n
        
        for i in range(n):
            batch = batches[i]
            
            # For each stage j from 1 to n-1 (0-based column index)
            # In task.md: j = 1..v-1 for ripening (1-based), j = v..n-1 for wilting (1-based)
            # In our 0-based code: j = 1..v-1 for ripening, j = v..n-1 for wilting
            # (j=0 is initial state, j=1..n-1 are transitions)
            
            for j in range(1, n):
                is_ripening = False
                if config.enable_ripening and v > 0:
                    # Ripening stages: j = 1..v-1 (0-based, matching task.md 1-based j=1..v-1)
                    # Wilting stages: j = v..n-1 (0-based, matching task.md 1-based j=v..n-1)
                    if 1 <= j <= v - 1:
                        is_ripening = True
                
                # Determine range for this coefficient
                if is_ripening:
                    # Ripening: b_{ij} \in (1, beta_max]
                    low, high = 1.0 + 1e-6, beta_max
                else:
                    # Wilting: b_{ij} \in [beta1, beta2] \subset (0,1)
                    low, high = config.beta1, config.beta2
                
                # Generate value
                if config.distribution_type == "concentrated":
                    if is_ripening:
                        # Use batch specific range for ripening
                        b_low = batch.beta_range_start_ripening if batch.beta_range_start_ripening else low
                        b_high = batch.beta_range_end_ripening if batch.beta_range_end_ripening else high
                        val = np.random.uniform(b_low, b_high)
                    else:
                        # Use batch specific range for wilting
                        b_low = batch.beta_range_start if batch.beta_range_start else low
                        b_high = batch.beta_range_end if batch.beta_range_end else high
                        val = np.random.uniform(b_low, b_high)
                else:
                    # Uniform distribution
                    val = np.random.uniform(low, high)
                    
                B[i, j] = val
                
        return B

    @staticmethod
    def generate_states(batches: List[BeetBatch], B: np.ndarray) -> np.ndarray:
        """
        Generates Matrix C (sugar content).
        c_{ij}
        Col 0: c_{i1} = a_i
        Col j: c_{ij} = c_{i, j-1} * B[i, j]
        """
        n = len(batches)
        C = np.zeros((n, n))
        
        # Initial state (j=0)
        for i in range(n):
            C[i, 0] = batches[i].initial_sugar
            
        # Subsequent states
        for j in range(1, n):
            for i in range(n):
                C[i, j] = C[i, j-1] * B[i, j]
                
        return C
