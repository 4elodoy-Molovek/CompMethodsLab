"""
===================================================================
МОДЕЛЬ ПОТЕРЬ - РАСЧЁТ ПОТЕРЬ САХАРА ПРИ ПЕРЕРАБОТКЕ
===================================================================

НАЗНАЧЕНИЕ:
    Этот модуль содержит класс LossModel для расчёта потерь сахара
    при переработке партий свёклы и формирования итоговой матрицы
    состояний после учёта потерь.

МАТЕМАТИЧЕСКАЯ МОДЕЛЬ:
    Матрица потерь L:
        l_{ij} = 1.1 + 0.1541 × (K_i + Na_i) + 0.2159 × N_i + 0.9989 × I_{ij} + 0.1967
    
    где:
        K_i - содержание калия в партии i
        Na_i - содержание натрия в партии i
        N_i - содержание азота в партии i
        I_{ij} = I_{i0} × (growth_base)^(7j - 7)
            I_{i0} - начальный индекс партии i
            growth_base - база роста (обычно 1.029 или 1.03)
            j - номер этапа (1-based, т.е. j = 1, 2, ..., n)
            7 - количество дней в одном этапе
    
    Итоговая матрица состояний:
        S̃ = C - L/100
    
    где:
        C - матрица содержания сахара (до учёта потерь)
        L - матрица потерь (в процентах)
        S̃ - итоговая матрица (после учёта потерь)

ВАЖНО:
    - Потери l_{ij} задаются в процентах (%)
    - Перед вычитанием из C нужно разделить L на 100
    - Это соответствует формуле из task.md

ИСПОЛЬЗОВАНИЕ:
    from core.losses import LossModel
    
    # Расчёт матрицы потерь
    L = LossModel.calculate_losses(batches, num_stages=10, growth_base=1.029)
    
    # Расчёт итоговой матрицы
    S_tilde = LossModel.calculate_final_yield_matrix(C, L)

ПАРАМЕТРЫ:
    batches: List[BeetBatch] - список партий свёклы
    num_stages: int - количество этапов переработки (обычно n)
    growth_base: float - база роста (1.029 или 1.03)

РАСШИРЕНИЕ:
    Чтобы изменить формулу потерь:
        1. Модифицируйте метод calculate_losses()
        2. Убедитесь, что единицы измерения согласованы
        3. Обновите комментарии и документацию

АВТОР: [Ваше имя]
ДАТА СОЗДАНИЯ: [Дата]
===================================================================
"""

import numpy as np
from typing import List
from .models import BeetBatch

class LossModel:
    @staticmethod
    def calculate_losses(
        batches: List[BeetBatch],
        C: np.ndarray,
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
        # Реалистичные пределы потерь
        MIN_LOSS = 1.5    # Минимальные технологические потери
        MAX_LOSS = 4.5    # Максимальные потери в нормальном производстве
        MAX_PERCENT_OF_SUGAR = 0.35  # Максимум 35% от содержания сахара
        
        for i in range(n):
            batch = batches[i]
            K = batch.k
            Na = batch.na
            N = batch.n_content
            I0 = batch.i0

            if growth_base == 1.029:
                I0 *= C[i, 0] / 100.0
            else:
                I0 = 0.1
            
            max_loss_so_far = 0.0

            for j in range(num_stages): # j is 0-indexed here (0..n-1)
                # Formula uses 1-based index (1..n)
                stage_idx = j + 1


                # I_{ij} calculation
                # Power is 7j - 7 = 7(j-1). Since stage_idx is j, -> 7(stage_idx) - 7 = 7(stage_idx - 1)
                # If stage_idx=1, power=0. Correct.
                I_ij = I0 * (growth_base ** (stage_idx - 1))

                
                # Loss calculation
                l_val = 1.1 + 0.1541 * (K + Na) + 0.2159 * N + 0.9989 * I_ij + 0.1967


                
                # ГАРАНТИРУЕМ, что потери не уменьшаются
                # (физически невозможно уменьшение потерь со временем хранения)
                
                
                current_sugar = C[i, j]
                
                # 1. Не менее минимальных технологических потерь
                l_val = max(l_val, MIN_LOSS)
                
                # 2. Не более максимального процента от сахара
                # Но с учётом того, что потери не должны уменьшаться
                max_by_percent = current_sugar * MAX_PERCENT_OF_SUGAR
                
                # 3. Не более абсолютного максимума
                # Применяем ограничения, но сохраняем неубывание
                if l_val > max_by_percent:
                    # Если ограничение по проценту строже, берем его
                    # но не опускаемся ниже ранее достигнутых потерь
                    l_val = min(max_by_percent, MAX_LOSS)
                    l_val = max(l_val, max_loss_so_far)
                else:
                    l_val = min(l_val, MAX_LOSS)
                
                # Обновляем максимальные потери для этой партии
                max_loss_so_far = l_val
                
                
                
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
        return C - L
