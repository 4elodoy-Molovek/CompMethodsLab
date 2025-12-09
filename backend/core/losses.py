import numpy as np
from typing import List
from .models import BeetBatch

class LossModel:
    @staticmethod
    def calculate_losses(
        batches: List[BeetBatch],
        num_stages: int,
        growth_base: float = 1.029,
    ) -> np.ndarray:
        """
        Calculates matrix L (losses) and returns it.
        l_{ij} formula:
        l_{ij} = 1.1 + 0.1541(K + Na) + 0.2159 N + 0.9989 I_{ij} + 0.1967
        I_{ij} = I_{i0} * (growth_base)^(7j - 7)
        where j is 1-based stage index.
        """
        n = len(batches)
        L = np.zeros((n, num_stages))
        
        for i in range(n):
            batch = batches[i]
            K = batch.k
            Na = batch.na
            N = batch.n_content
            I0 = batch.i0
            
            for j in range(num_stages): # j is 0-indexed here (0..n-1)
                # Formula uses 1-based index (1..n)
                stage_idx = j + 1
                
                # I_{ij} calculation
                # Power is 7j - 7 = 7(j-1). Since stage_idx is j, -> 7(stage_idx) - 7 = 7(stage_idx - 1)
                # If stage_idx=1, power=0. Correct.
                I_ij = I0 * (growth_base ** (7 * (stage_idx - 1)))
                
                # Loss calculation
                l_val = 1.1 + 0.1541 * (K + Na) + 0.2159 * N + 0.9989 * I_ij + 0.1967
                L[i, j] = l_val
                
        return L

    @staticmethod
    def calculate_final_yield_matrix(C: np.ndarray, L: np.ndarray) -> np.ndarray:
        """
        Calculates S_tilde = C - L_tilde
        The task says l_{ij} is in %.
        "l_{ij} (v %) mozet byt vychisleno..."
        "S_tilde = C - L_tilde"
        We assume L_tilde is the absolute loss.
        But wait, usually loss in % means % of current sugar? Or just subtract percentage points?
        Task: "S_tilde = C - L_tilde" implies simple subtraction.
        However, C is "amount of useful ingredient" (mass/share?). 
        Task says: "c_{i1} = a_i \in [a_min, a_max]" (share).
        So C contains percentages/shares (e.g. 15%).
        If L contains percentages (e.g. 1.5%), then subtraction makes sense.
        So we divide L by 100 before subtracting from C (отталкивался от комментария в мдшке "я так понимаю надо l_{ij} поделить на 100 и можно с исходной C считать")
        """
        return C - L / 100.0
