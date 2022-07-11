from dataclasses import dataclass
from typing import List

import numpy as np

@dataclass
class Config:
    smooth_x: bool = False
    smooth_y: bool = False
    cov_threshold: float = 0.1
    moving_average_count: int = 5
    max_tangent_length: int = 15  # Cantidad de puntos tomados para calcular la pendiente
    normal_line_length: int = 20

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
class TrackingFrameResult:
    points:         List[TrackingPoint]
    none_points:    List[TrackingPoint]
    normal_lines:   List[TrackingSegment]  # Cada linea normal esta definida por sus dos extremos

@dataclass
class TrackingResult:
    frames: List[TrackingFrameResult]

@dataclass
class ApplicationError(Exception):
    message: str
    code: int = 50_000
