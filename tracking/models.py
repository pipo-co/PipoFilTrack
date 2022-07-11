from dataclasses import dataclass, fields, field, Field
from enum import Enum
from typing import List, Optional, Tuple

import numpy as np

@dataclass
class ApplicationError(Exception):
    message: str
    code: int = 50_000

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

# Encode tracking point extraordinary statuses
class TrackingPointStatus(str, Enum):
    INTERPOLATED    = 'INTERPOLATED'
    DELETED         = 'DELETED'

@dataclass
class TrackingPoint:
    x: float
    y: float
    # TODO: Se manda siempre como null :((. No puede quedar asi. O sacarlo de aca, o libreria con mejor deserializacion.
    status: Optional[TrackingPointStatus] = None

    @classmethod
    def from_arrays(cls, points_by_status: List[Tuple[np.ndarray, Optional[TrackingPointStatus]]]) -> List['TrackingPoint']:
        return [cls.from_array(point, status) for points, status in points_by_status for point in points]

    @classmethod
    def from_array(cls, point: np.ndarray, status: Optional[TrackingPointStatus] = None) -> 'TrackingPoint':
        return cls(float(point[0]), float(point[1]), status)

# Un segmento se define por sus 2 extremos
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
class TrackingFrameMetadata:
    normal_lines: List[TrackingSegment] = field(default_factory=list)

@dataclass
class TrackingFrameResult:
    points:     List[TrackingPoint]
    metadata:   TrackingFrameMetadata

@dataclass
class TrackingResult:
    frames: List[TrackingFrameResult]
