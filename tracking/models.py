from dataclasses import dataclass
from enum import Enum
from typing import List

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
    def from_str(cls, val: str):
        if val is None or val not in cls.values():
            return cls.ALL
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
class TrackingPoint:
    x: float
    y: float

    @classmethod
    def from_arrays(cls, points: np.ndarray) -> List['TrackingPoint']:
        return [cls.from_array(point) for point in points]

    @classmethod
    def from_array(cls, point: np.ndarray) -> 'TrackingPoint':
        return cls(float(point[0]), float(point[1]))

@dataclass
class TrackingSegment:
    start:  TrackingPoint
    end:    TrackingPoint

    @classmethod
    def from_arrays(cls, segments: np.ndarray) -> List['TrackingSegment']:
        return [cls.from_array(segment) for segment in segments]

    @classmethod
    def from_array(cls, segment: np.ndarray) -> 'TrackingSegment':
        return cls(TrackingPoint.from_array(segment[0]), TrackingPoint.from_array(segment[1]))

@dataclass
class TrackingResult:
    points:         List[TrackingPoint]
    none_points:    List[TrackingPoint]
    normal_lines:   List[TrackingSegment]  # Cada linea normal esta definida por sus dos extremos

@dataclass
class ApplicationError(Exception):
    message: str
    code: int = 50_000
