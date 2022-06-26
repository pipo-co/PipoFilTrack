from dataclasses import dataclass
from distutils.command.config import config
import math
from itertools import tee
from typing import List, Optional, Tuple, Union

import numpy as np
import skimage as skimg
from scipy.optimize import curve_fit
from scipy.stats import kstest, normaltest

from tracking.models import Config

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

def indexes_to_points(brightest_point_profile_index: np.ndarray, normal_lines: np.ndarray, prev_frame_points: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
  valid_values = []
  invalid_values = []
  counter = 0
  none_flag = False
  previous_point: Tuple[int, int]
  for bp, nl in zip(brightest_point_profile_index, normal_lines):
    value = index_to_point(bp, nl)
    if value:
      if none_flag:
        none_flag = False
        interpolation = points_linear_interpolation(np.asarray(previous_point), np.asarray(value))[1:]
        valid_values.extend(interpolation)
        invalid_values.extend(interpolation)
      else:
        valid_values.append(value)
    else:
      if none_flag:
        counter+=1
      else:
        none_flag = True
        previous_point = valid_values[-1]
        counter=1

  return np.array(valid_values), np.array(invalid_values)
    

def index_to_point(point_values: Tuple[float, float], points: np.ndarray) -> Optional[Tuple[float, float]]:
    """
        Obtener las coordenadas de un punto ubicado entre otros dos.
        Si no esta contenido en la lista de puntos se ignora (None)
    """
    idx = point_values[0]

    # TODO(tobi): habilitarlo por config 
    if point_values[1] > 0.2 or int(idx) + 1 >= len(points):
        return None

    start = points[int(idx)]
    end = points[int(idx)+1] 
    delta = idx - int(idx)

    new_x = start[0] + delta * (end[0] - start[0])
    new_y = start[1] + delta * (end[1] - start[1])

    return (new_x, new_y)

def gaussian(x, mu, sig):
    return 1./(np.sqrt(2.*np.pi)*sig)*np.exp(-np.power((x - mu)/sig, 2.)/2)

def gauss_fitting(intensity_profile: np.ndarray, max_color: int) -> np.ndarray:
    xdata = np.arange(len(intensity_profile))
    f = lambda x, m, s: gaussian(x, m, s) * max_color
    popt, pcov = curve_fit(f, xdata, intensity_profile)
    p_error = np.square(np.diag(pcov))
  
    return popt[0], p_error[0]


# def adjust_points(brightest_points: List[Tuple[float, float]], previous_points: np.ndarray) -> np.ndarray:
#     return_list = []
#     max_index = len(brightest_points) - 2
#     for i, (bp, pp) in enumerate(zip(brightest_points, previous_points)):
#       if bp:
#         return_list.append(bp)
#       elif i > 1 and i < max_index:
        
#         previous_point_x: float
#         previous_point_y: float

#         if brightest_points[i-1]:
#           previous_point_x = brightest_points[i-1][0] 
#           previous_point_y = brightest_points[i-1][1] 
#         else: 
#           previous_point_x = previous_points[i-1][0] 
#           previous_point_y = previous_points[i-1][1] 

#         next_point_x: float
#         next_point_y: float

#         if brightest_points[i+1]:
#           next_point_x = brightest_points[i+1][0] 
#           next_point_y = brightest_points[i+1][1] 
#         else: 
#           next_point_x = previous_points[i+1][0] 
#           next_point_y = previous_points[i+1][1] 

#         new_x = np.mean([previous_point_x, pp[0], next_point_x])
#         new_y = np.mean([previous_point_y, pp[1], next_point_y])
  
#         return_list.append((int(new_x), int(new_y)))
#       else:
#         return_list.append(pp)

#     return np.asarray(return_list)


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
