from dataclasses import dataclass, fields, field, Field
from enum import Enum
from typing import List, Optional, Dict, Iterable

import numpy as np

@dataclass
class ApplicationError(Exception):
    message: str
    code: int = 50_000

def bool_config_field(default: bool, name: str, desc: str) -> bool:
    return field(default=default, metadata={'name': name, 'desc': desc})

def int_config_field(default: int, name: str, desc: str, min_: int, max_: int) -> int:
    return field(default=default, metadata={'min': min_, 'max': max_, 'name': name, 'desc': desc})

def float_config_field(default: float, name: str, desc: str, step: float, min_: float, max_: float) -> float:
    return field(default=default, metadata={'step': step, 'min': min_, 'max': max_, 'name': name, 'desc': desc})

@dataclass
class Config:
    max_fitting_error: float    = float_config_field(0.2, 'Tolerancia de error', 'Limite de tolerancia en el error del ajuste gaussiano del perfil de intensidad', step=0.01, min_=0, max_=100)
    normal_line_length: int     = int_config_field(10, 'Ancho del perfil de intensidad', 'Ancho en pixeles del perfil de intensidad a tomar perpendicularmente a cada punto', min_=2, max_=100)
    point_density: int          = int_config_field(1, 'Densidad de puntos', 'Proporción de puntos a usar durante la interpolación por pixel (1/n). La máxima densidad es 1. Reducir la densidad reduce la precisión, pero aumenta la velocidad del algoritmo', min_=1, max_=100)
    missing_inter_len: int      = int_config_field(3, 'Cantidad de puntos para interpolar', 'Cantidad de puntos vecinos a tomar hacia ambos lados para interpolar los puntos considerados inválidos (rojos)', min_=1, max_=20)
    max_tangent_length: int     = int_config_field(15, 'Puntos para calcular tangente', 'Cantidad de puntos vecinos tomados para calcular la pendiente de cada punto', min_=1, max_=100)
    bezier_segment_len: int     = int_config_field(100, 'Longitud del segmento de suavizado', 'Longitud por el que se parte el filamento, para luego ajustar a una curva de Bezier cada uno', min_=2, max_=500)
    bezier_smoothing: bool      = bool_config_field(True, 'Suavizado final', 'Post-procesamiento de suavizado del filamento ajustando a una curva de Bezier por segmento')

    @classmethod
    def from_dict(cls, env):
        env = env.copy()
        fields_dict = {f.name: f for f in fields(cls)}
        for k, v in fields_dict.items():
            if v.type == bool:
                env[k] = k in env
        return cls(**{k: fields_dict[k].type(v) for k, v in env.items() if k in fields_dict})

# Encode tracking point extraordinary statuses
class TrackingPointStatus(str, Enum):
    INTERPOLATED    = 'INTERPOLATED'
    PRESERVED       = 'PRESERVED'

@dataclass
class TrackingPoint:
    x: float
    y: float
    status: Optional[TrackingPointStatus] = None

    @classmethod
    def from_arrays(cls, points: np.ndarray, status_map: Dict[TrackingPointStatus, Iterable[int]]) -> List['TrackingPoint']:
        ret = [cls.from_array(point) for point in points]

        # Asignamos los status correspondientes segun el mapa
        for status, points_idx in status_map.items():
            for point_idx in points_idx:
                ret[point_idx].status = status

        return ret

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
    errors: List[str] = field(default_factory=list)
