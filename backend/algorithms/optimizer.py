"""
===================================================================
АЛГОРИТМЫ ОПТИМИЗАЦИИ - ПОИСК ОПТИМАЛЬНОЙ ПОСЛЕДОВАТЕЛЬНОСТИ
===================================================================

НАЗНАЧЕНИЕ:
    Этот модуль содержит класс Optimizer с различными алгоритмами
    оптимизации последовательности переработки партий свёклы.
    
    Задача: найти перестановку σ чисел от 1 до n, максимизирующую
    S(σ) = Σ_{j=1}^{n} S̃_{σ(j), j}

РЕАЛИЗОВАННЫЕ СТРАТЕГИИ:

    1. Жадная (Greedy):
       На каждом этапе j выбирает партию i с максимальным S[i, j]
       Сложность: O(n²)
    
    2. Бережливая (Thrifty):
       На каждом этапе j выбирает партию i с минимальным S[i, j]
       Сложность: O(n²)
    
    3. Бережливая/Жадная (Thrifty/Greedy):
       Первые (n-ν) этапов - бережливая стратегия
       С этапа ν - жадная стратегия
       По умолчанию ν = [n/2]
    
    4. Жадная/Бережливая (Greedy/Thrifty):
       Первые (n-ν) этапов - жадная стратегия
       С этапа ν - бережливая стратегия
    
    5. T(k)G (БkЖ):
       Первые (n-ν) этапов: выбирает k-ю позицию из отсортированного списка
       С этапа ν: жадная стратегия
       k должно удовлетворять: 1 ≤ k ≤ n - ν + 1
    
    6. Gk (вариация жадной):
       Измерения перед первым этапом и после этапов, кратных k
       Выбирает k партий с наивысшей сахаристостью
       Обрабатывает их в порядке убывания
       G1 = жадная, Gn = сортировка по начальной сахаристости
    
    7. Венгерский алгоритм (Optimal):
       Точный алгоритм решения задачи о назначениях
       Даёт оптимальное решение S*
       Использует scipy.optimize.linear_sum_assignment
       Сложность: O(n³)
    
    8. Случайная (Random):
       Случайная перестановка (базовая линия для сравнения)

ИСПОЛЬЗОВАНИЕ:
    from algorithms.optimizer import Optimizer
    import numpy as np
    
    # S_tilde - матрица состояний (n × n)
    S_tilde = np.array([[...], [...]])
    
    # Жадная стратегия
    permutation, yield_value = Optimizer.optimize_greedy(S_tilde)
    
    # Венгерский алгоритм (оптимальное решение)
    permutation, yield_value = Optimizer.optimize_hungarian(S_tilde)
    
    # Расчёт итоговой массы
    mass = Optimizer.calculate_final_mass(yield_value, mass_per_batch=1000.0)

ФОРМАТ РЕЗУЛЬТАТОВ:
    Все методы возвращают кортеж (permutation, total_yield):
        permutation: List[int] - перестановка (последовательность номеров партий, 0-based)
        total_yield: float - суммарный выход сахара S(σ)

ВАЖНО:
    - Индексы в permutation начинаются с 0 (0-based)
    - В математической модели используются 1-based индексы
    - При выводе пользователю может потребоваться преобразование: i + 1

РАСШИРЕНИЕ:
    Чтобы добавить новую стратегию:
        1. Создайте статический метод @staticmethod
        2. Сигнатура: def optimize_new_strategy(S_matrix: np.ndarray, ...) -> Tuple[List[int], float]
        3. Верните (permutation, total_yield)
        4. Добавьте вызов в app.py в функции optimize()

АВТОР: [Ваше имя]
ДАТА СОЗДАНИЯ: [Дата]
===================================================================
"""

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
        return (yield_value / 100.0) * mass_per_batch * days_per_stage

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
    def optimize_hungarian(S_matrix: np.ndarray) -> Tuple[List[int], float]:
        """
        Hungarian algorithm for optimal solution (absolute maximum).
        Uses scipy.optimize.linear_sum_assignment for assignment problem.
        This gives the theoretical maximum S*.
        """
        try:
            # Импортируем венгерский алгоритм из scipy
            # type: ignore - игнорируем предупреждение линтера о неразрешённом импорте
            # (scipy может быть не установлен, но код обрабатывает это через try-except)
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
    
    @staticmethod
    def optimize_hungarian_min(S_matrix: np.ndarray) -> Tuple[List[int], float]:
        try:
            from scipy.optimize import linear_sum_assignment  # type: ignore
        except ImportError:
            # Fallback: use greedy if scipy not available
            return Optimizer.optimize_greedy(S_matrix)
        
        # Hungarian algorithm solves minimization directly — no negation needed
        row_indices, col_indices = linear_sum_assignment(S_matrix)
        
        n = S_matrix.shape[0]
        permutation = [0] * n
        total_cost = 0.0

        for i in range(len(row_indices)):
            row = row_indices[i]
            col = col_indices[i]
            permutation[col] = row
            total_cost += S_matrix[row, col]
        
        return permutation, total_cost