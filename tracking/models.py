from dataclasses import dataclass, fields, field, Field
from typing import List

import numpy as np

def config_field(default, description) -> Field:
    return field(default=default, metadata={'description': description})

@dataclass
class Config:
    smooth_x: bool              = config_field(False,   'Post-procesamiento de suavizado en la coordenada Y')
    smooth_y: bool              = config_field(False,   'Post-procesamiento de suavizado en la coordenada X')
    cov_threshold: float        = config_field(0.2,     'Limite de tolerancia para el error en el ajuste gaussiano del perfil de intensidad')
    moving_average_count: int   = config_field(5,       'Cantidad de puntos a tomar para el moving average durante la rutina de suavizado')
    max_tangent_length: int     = config_field(15,      'Cantidad de puntos tomados para calcular la pendiente')
    normal_line_length: int     = config_field(15,      'Longitud en pixeles del perfil de intensidad a tomar')

    @classmethod
    def from_dict(cls, env):
        fields_dict = {f.name: f for f in fields(cls)}
        return cls(**{k: fields_dict[k].type(v) for k, v in env.items() if k in fields_dict})

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
