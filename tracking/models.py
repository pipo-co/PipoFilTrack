from dataclasses import dataclass
from enum import Enum
from typing import Optional

import numpy as np

class TrackStep(Enum):
    INTERPOLATION   = "interpolation"
    FILTER          = "filter"
    NORMAL          = "normal"
    ALL             = "all"

    @classmethod
    def values(cls):
        return list(map(lambda c: c.value, cls))

    @classmethod
    def from_str(cls, val):
        if val not in cls.values():
            raise ValueError(f'"{val}" is not a supported track step')
        return cls(val)

@dataclass
class Config:
    smooth_x: bool = False
    smooth_y: bool = False
    cov_threshold: float = 0.1
    moving_average_count: int = 5
    max_tangent_length: int = 15  # Cantidad de puntos tomados para calcular la pendiente
    normal_line_length: int = 20
    up_to_step: TrackStep = TrackStep.ALL

@dataclass
class Result:
    points: np.ndarray
    none_points: Optional[np.ndarray]
    frame: str
    normal_lines: Optional[np.ndarray] # Cada linea normal esta definida por sus dos extremos

@dataclass
class DisplayConfig:
    scatter: bool = True
    normal_lines: bool = False
    invalid_values: bool = True
