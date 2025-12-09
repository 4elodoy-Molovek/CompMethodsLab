from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class BeetBatch:
    index: int
    initial_sugar: float  # a_i
    k: float              # K_i
    na: float             # Na_i
    n_content: float      # N_i
    i0: float             # I_i0
    
    # Optional parameters for concentrated distribution (wilting)
    delta: Optional[float] = None
    beta_range_start: Optional[float] = None  # beta_i^1
    beta_range_end: Optional[float] = None    # beta_i^2
    
    # Optional parameters for concentrated distribution (ripening)
    delta_ripening: Optional[float] = None
    beta_range_start_ripening: Optional[float] = None
    beta_range_end_ripening: Optional[float] = None

@dataclass
class ExperimentConfig:
    n: int  # Number of batches
    m: float # Mass per batch
    
    # Global ranges for random generation
    a_min: float
    a_max: float
    
    # Degradation parameters
    beta1: float
    beta2: float
    distribution_type: str # "uniform" or "concentrated"
    
    # Ripening parameters
    enable_ripening: bool = False
    v: Optional[int] = None # Number of ripening stages
    beta_max: Optional[float] = None # Max coefficient for ripening

    # Losses and growth model
    use_losses: bool = True
    growth_base: float = 1.029

    # Concentrated distribution control (delta bounds)
    delta_k: float = 4.0  # denominator for |beta2 - beta1| / k (wilting)
    delta_k_ripening: float = 4.0  # denominator for |beta_max - 1| / k (ripening)
    
    # Loss parameter ranges
    k_min: float = 4.8
    k_max: float = 7.05
    na_min: float = 0.21
    na_max: float = 0.82
    n_content_min: float = 1.58
    n_content_max: float = 2.8
    i0_min: float = 0.62
    i0_max: float = 0.64
