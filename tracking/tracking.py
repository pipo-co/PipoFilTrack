import math
from itertools import tee
from typing import List, Optional, Tuple, Union

import numpy as np
import skimage as skimg
from scipy.optimize import curve_fit

PIXEL_POINT_RATIO=1

def multi_point_linear_interpolation(points: np.ndarray, pixel_point_ratio: int = PIXEL_POINT_RATIO) -> np.ndarray:
    """
    Given a point vector, interpolates linearly between each point pair.
    """
    return np.append(np.concatenate([points_linear_interpolation(start, end)[:-1] for start, end in zip(points, points[1:])]), [points[-1]], axis=0)

def points_linear_interpolation(start: Tuple[int, int], end: Tuple[int, int]) -> np.ndarray:
    # line returns the pixels of the line described by the 2 points
    # https://scikit-image.org/docs/stable/api/skimage.draw.html#line
    # Nota(tobi): Aca hay una bocha de truquito, lo podemos simplificar
    return np.stack(skimg.draw.line(*start.astype(int), *end.astype(int)), axis=-1)

def index_to_point(idx: float, points: np.ndarray) -> Optional[Tuple[float, float]]:
    """
        Obtener las coordenadas de un punto ubicado entre otros dos.
        Si no esta contenido en la lista de puntos se ignora (None)
    """
    
    # TODO(tobi): habilitarlo por config 
    if int(idx)+1 >= len(points):
        return None

    start = points[int(idx)]
    end = points[int(idx)+1] 
    delta = idx - int(idx)

    new_x = start[0] + delta * (end[0] - start[0])
    new_y = start[1] + delta * (end[1] - start[1])

    return new_x, new_y

def gaussian(x, mu, sig):
    return 1./(np.sqrt(2.*np.pi)*sig)*np.exp(-np.power((x - mu)/sig, 2.)/2)

def gauss_fitting(intensity_profile: np.ndarray, max_color: int) -> np.ndarray:
    xdata = np.arange(len(intensity_profile))
    popt, _ = curve_fit(lambda x, m, s: gaussian(x, m, s) * max_color, xdata, intensity_profile)

    return popt

def generate_normal_line_bounds(points: np.ndarray, angle_resolution: int, normal_len: float) -> np.ndarray:
    
    d = angle_resolution

    start = points[:-d]
    end = points[d:]

    tangent_angle = np.arctan2(end[:,1] - start[:,1], end[:,0] - start[:,0])
    
    normal_angle = np.zeros(len(points))
    normal_angle[d//2:-d//2] = tangent_angle + np.pi/2
    normal_angle[:d//2] = normal_angle[d//2]
    normal_angle[-d//2:] = normal_angle[-d//2 -1]

    # Seno y coseno de la normal. Usados para generar los limites de la misma 
    component_multiplier = np.stack((np.cos(normal_angle), np.sin(normal_angle)), axis=1)
    upper = points + component_multiplier * normal_len / 2
    lower = points - component_multiplier * normal_len / 2

    bounds = np.stack((upper, lower), axis=1)

    return np.rint(bounds).astype(np.int64)
