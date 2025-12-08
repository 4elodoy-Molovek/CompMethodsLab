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
        
        for i in range(n):
            batch = batches[i]
            
            # For each stage j from 1 to n-1 (0-based)
            # Stage 0 is t=1 (initial). Stage 1 is t=2.
            # b_{i, "j-1"} in formula corresponds to transition to stage j.
            # Task: j=2..n. formula b_{i, j-1}.
            # If j=2 (step 2), we need b_{i, 1}.
            
            for j in range(1, n):
                is_ripening = False
                if config.enable_ripening:
                    # Ripening stages: 1 to v-1
                    # In 0-index: j corresponds to stage j+1.
                    # So stages 2 to v corresponds to j=1 to j=v-1.
                    # Wait, task says: j = 1..v-1 for ripening PARAMETERS.
                    # But b param indices are shifted?
                    # Task: "Na etapah dozarivaniya parametry b_{ij} ... j = 1..v-1"
                    # And "Na etapah uvyadaniya ... j = v..n-1"
                    # These indexes likely refer to the 'step' index of the coefficient itself.
                    # Since we are iterating j from 1 to n-1 as the column index of our matrix:
                    # Let's map directly.
                    if 1 <= j <= v - 1:
                        is_ripening = True
                
                # Determine range for this coefficient
                low, high = config.beta1, config.beta2
                if is_ripening:
                    low, high = 1.0 + 1e-6, config.beta_max # (1, beta_max]
                
                # Generate value
                if config.distribution_type == "concentrated" and not is_ripening:
                    # Use batch specific range
                    # Ensure range is valid
                    b_low = batch.beta_range_start if batch.beta_range_start else low
                    b_high = batch.beta_range_end if batch.beta_range_end else high
                    val = np.random.uniform(b_low, b_high)
                else:
                    # Uniform
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
