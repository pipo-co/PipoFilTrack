import math
from itertools import tee
from typing import List, Tuple, Union

import numpy as np
import skimage as skimg
from scipy.optimize import curve_fit

from tracking.types_utils import Point

PIXEL_POINT_RATIO=1

def circle_coordinate(start: Point, angle: float, radius: float) -> Point:
    """
        Returns a new point that is the result of traversing from `start`,
         in the direction of `angle` for distance `radius`
    """
    x = start.x + math.cos(angle) * radius
    y = start.y + math.sin(angle) * radius
    return Point(int(x), int(y))


def adjust_points(img, points: np.ndarray, normal_len: float, angle_resolution: int) -> np.ndarray:
    # TODO(tobi): normal_len deberia estar estar expresado en pixeles??
    # TODO(tobi): pasar el algoritmo a ndarray. Por ahora hacemos la traduccion de manera interna
    
    normal_lines_bounds = generate_normal_line_bounds(points, angle_resolution, normal_len)
    # No todas salen con la misma longitud
    normal_lines = [points_linear_interpolation(start, end) for start, end in normal_lines_bounds]
    intensity_profiles = map(lambda nl: img[nl[:,1], nl[:,0]], normal_lines)
    brightest_point_profile_index = map(lambda ip: gauss_fitting(ip, img.max())[0], intensity_profiles)
    brightest_point = np.array([index_to_point(idx, nl) for idx, nl in zip(brightest_point_profile_index, normal_lines)])
    
    # TODO: ver como y/o cuando se guardan los valores precisos, mientras tanto se trabaja con valores discretos
    return np.rint(brightest_point).astype(int), normal_lines_bounds


def multi_point_linear_interpolation(points: np.ndarray, pixel_point_ratio: int = PIXEL_POINT_RATIO) -> np.ndarray:
    """
    Given a point vector, interpolates linearly between each point pair.
    """
    return np.append(np.concatenate([points_linear_interpolation(start, end)[:-1] for start, end in zip(points, points[1:])]), [points[-1]], axis=0)

def points_linear_interpolation(start: Tuple[int, int], end: Tuple[int, int]) -> np.ndarray:
    # line returns the pixels of the line described by the 2 points
    # https://scikit-image.org/docs/stable/api/skimage.draw.html#line
    # Nota(tobi): Aca hay una bocha de truquito, lo podemos simplificar
    return np.stack(skimg.draw.line(*start, *end), axis=-1)

def index_to_point(idx: float, points: np.ndarray) -> Tuple[float, float]:
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

    section_angle = np.arctan2(end[:,1] - start[:,1], end[:,0] - start[:,0])
    
    normal_angle = np.zeros(len(points))
    normal_angle[d//2:-d//2] = section_angle + np.pi/2
    normal_angle[:d//2] = normal_angle[d//2]
    normal_angle[-d//2:] = normal_angle[-d//2 -1]

    component_multiplier = np.stack((np.cos(normal_angle), np.sin(normal_angle)), axis=1)
    upper = points + component_multiplier * normal_len / 2
    lower = points - component_multiplier * normal_len / 2
    
    bounds = np.stack((upper, lower), axis=1)

    return np.rint(bounds).astype(np.int64)
