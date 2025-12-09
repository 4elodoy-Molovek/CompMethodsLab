import numpy as np
from typing import List, Tuple, Optional
import random

class Optimizer:
    @staticmethod
    def calculate_final_mass(yield_value: float, mass_per_batch: float, days_per_stage: int = 7) -> float:
        """
        Calculates final product mass according to task.md:
        S = S(σ) × M × d, where d is number of days per stage (7).
        """
        return yield_value * mass_per_batch * days_per_stage

    @staticmethod
    def optimize_thrifty(S_matrix: np.ndarray) -> Tuple[List[int], float]:
        """
        Thrifty strategy (бережливая):
        At each step j (column), pick the available row i with the MINIMUM value S[i, j].
        Returns permutation and total yield.
        """
        n = S_matrix.shape[0]
        available_rows = set(range(n))
        permutation = []
        total_yield = 0.0

        for j in range(n):
            best_row = -1
            min_val = float('inf')

            for row in available_rows:
                val = S_matrix[row, j]
                if val < min_val:
                    min_val = val
                    best_row = row

            permutation.append(best_row)
            available_rows.remove(best_row)
            total_yield += min_val

        return permutation, total_yield

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

    @staticmethod
    def optimize_thrifty_greedy(S_matrix: np.ndarray, nu: Optional[int] = None) -> Tuple[List[int], float]:
        """
        Strategy 3: Thrifty/Greedy (Бережливая/жадная)
        First (n-nu) stages use thrifty, then from stage nu use greedy.
        nu = [n/2] by default.
        """
        n = S_matrix.shape[0]
        if nu is None:
            nu = n // 2
        
        available_rows = set(range(n))
        permutation = []
        total_yield = 0.0
        
        for j in range(n):
            if j < n - nu:
                # Thrifty: pick minimum
                best_row = -1
                min_val = float('inf')
                for row in available_rows:
                    val = S_matrix[row, j]
                    if val < min_val:
                        min_val = val
                        best_row = row
                total_yield += min_val
            else:
                # Greedy: pick maximum
                best_row = -1
                max_val = -float('inf')
                for row in available_rows:
                    val = S_matrix[row, j]
                    if val > max_val:
                        max_val = val
                        best_row = row
                total_yield += max_val
            
            permutation.append(best_row)
            available_rows.remove(best_row)
        
        return permutation, total_yield

    @staticmethod
    def optimize_greedy_thrifty(S_matrix: np.ndarray, nu: Optional[int] = None) -> Tuple[List[int], float]:
        """
        Strategy 4: Greedy/Thrifty (Жадная/бережливая)
        First (n-nu) stages use greedy, then from stage nu use thrifty.
        nu = [n/2] by default.
        """
        n = S_matrix.shape[0]
        if nu is None:
            nu = n // 2
        
        available_rows = set(range(n))
        permutation = []
        total_yield = 0.0
        
        for j in range(n):
            if j < n - nu:
                # Greedy: pick maximum
                best_row = -1
                max_val = -float('inf')
                for row in available_rows:
                    val = S_matrix[row, j]
                    if val > max_val:
                        max_val = val
                        best_row = row
                total_yield += max_val
            else:
                # Thrifty: pick minimum
                best_row = -1
                min_val = float('inf')
                for row in available_rows:
                    val = S_matrix[row, j]
                    if val < min_val:
                        min_val = val
                        best_row = row
                total_yield += min_val
            
            permutation.append(best_row)
            available_rows.remove(best_row)
        
        return permutation, total_yield

    @staticmethod
    def optimize_tkg(S_matrix: np.ndarray, k: int, nu: Optional[int] = None) -> Tuple[List[int], float]:
        """
        Strategy 5: T(k)G (БkЖ)
        First (n-nu) stages: pick k-th position from sorted (ascending) by sugar content.
        From stage nu: use greedy.
        k must satisfy: 1 <= k <= n - nu + 1
        nu = [n/2] by default.
        """
        n = S_matrix.shape[0]
        if nu is None:
            nu = n // 2
        
        if k < 1 or k > n - nu + 1:
            k = 1  # fallback to thrifty
        
        available_rows = set(range(n))
        permutation = []
        total_yield = 0.0
        
        for j in range(n):
            if j < n - nu:
                # Pick k-th from sorted (ascending)
                row_values = [(row, S_matrix[row, j]) for row in available_rows]
                row_values.sort(key=lambda x: x[1])  # sort by value ascending
                
                k_idx = min(k - 1, len(row_values) - 1)  # k-th position (1-based -> 0-based)
                best_row = row_values[k_idx][0]
                total_yield += row_values[k_idx][1]
            else:
                # Greedy: pick maximum
                best_row = -1
                max_val = -float('inf')
                for row in available_rows:
                    val = S_matrix[row, j]
                    if val > max_val:
                        max_val = val
                        best_row = row
                total_yield += max_val
            
            permutation.append(best_row)
            available_rows.remove(best_row)
        
        return permutation, total_yield

    @staticmethod
    def optimize_gk(S_matrix: np.ndarray, k: int) -> Tuple[List[int], float]:
        """
        Strategy Gk: Variation of greedy strategy
        Measurements before first stage and after stages divisible by k.
        Select k batches with highest sugar content, process them in descending order.
        G1 = greedy, Gn = C1 (sorted by initial sugar descending).
        """
        n = S_matrix.shape[0]
        permutation = []
        total_yield = 0.0
        available_rows = set(range(n))
        
        # Measurement stages: 0, k, 2k, 3k, ...
        measurement_stages = [0]
        stage = k
        while stage < n:
            measurement_stages.append(stage)
            stage += k
        
        # Process in batches
        current_stage = 0
        for meas_stage in measurement_stages:
            # Determine how many batches to select
            remaining = len(available_rows)
            if remaining <= 1:
                break
            
            # Select batches for next k stages (or remaining)
            stages_to_process = min(k, n - current_stage, remaining)
            
            # Get current values for available rows at measurement stage
            row_values = [(row, S_matrix[row, meas_stage]) for row in available_rows]
            row_values.sort(key=lambda x: x[1], reverse=True)  # descending
            
            # Select top batches
            selected = row_values[:stages_to_process]
            
            # Process them in order (descending sugar)
            for i, (row, _) in enumerate(selected):
                if current_stage >= n:
                    break
                permutation.append(row)
                total_yield += S_matrix[row, current_stage]
                available_rows.remove(row)
                current_stage += 1
        
        # Process any remaining batches with greedy
        for j in range(current_stage, n):
            if not available_rows:
                break
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
    def optimize_hungarian(S_matrix: np.ndarray) -> Tuple[List[int], float]:
        """
        Hungarian algorithm for optimal solution (absolute maximum).
        Uses scipy.optimize.linear_sum_assignment for assignment problem.
        This gives the theoretical maximum S*.
        """
        try:
            from scipy.optimize import linear_sum_assignment  # type: ignore
        except ImportError:
            # Fallback: use greedy if scipy not available
            return Optimizer.optimize_greedy(S_matrix)
        
        # Hungarian algorithm solves minimization, so we negate the matrix
        row_indices, col_indices = linear_sum_assignment(-S_matrix)
        
        # Build permutation (col_indices[i] is the column assigned to row i)
        # But we need: at stage j, which row is processed?
        n = S_matrix.shape[0]
        permutation = [0] * n
        total_yield = 0.0
        
        for i in range(len(row_indices)):
            row = row_indices[i]
            col = col_indices[i]
            permutation[col] = row
            total_yield += S_matrix[row, col]
        
        return permutation, total_yield
