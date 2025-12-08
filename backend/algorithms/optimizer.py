import numpy as np
from typing import List, Tuple
import random

class Optimizer:
    @staticmethod
    def optimize_greedy(S_matrix: np.ndarray) -> Tuple[List[int], float]:
        """
        Greedy strategy:
        At each step j (column), pick the available row i that has the maximum value S[i, j].
        Returns permutation (list of batch indices) and total yield.
        Indices are 0-based.
        """
        n = S_matrix.shape[0]
        available_rows = set(range(n))
        permutation = []
        total_yield = 0.0
        
        for j in range(n):
            # Find best row for this column j among available
            best_row = -1
            max_val = -float('inf')
            
            for row in available_rows:
                val = S_matrix[row, j]
                if val > max_val:
                    max_val = val
                    best_row = row
            
            permutation.append(best_row)
            available_rows.remove(best_row)
            total_yield += max_val
            
        return permutation, total_yield

    @staticmethod
    def optimize_random(S_matrix: np.ndarray) -> Tuple[List[int], float]:
        n = S_matrix.shape[0]
        permutation = list(range(n))
        random.shuffle(permutation)
        
        total_yield = 0.0
        for j in range(n):
            row = permutation[j]
            total_yield += S_matrix[row, j]
            
        return permutation, total_yield
