from typing import  List, Optional, Tuple

import numpy as np
import skimage as skimg
from scipy.optimize import curve_fit

PIXEL_POINT_RATIO=1

def multi_point_linear_interpolation(points: np.ndarray, pixel_point_ratio: int = PIXEL_POINT_RATIO) -> np.ndarray:
    """
    Given a point vector, interpolates linearly between each point pair.
    """
    return np.append(np.concatenate([points_linear_interpolation(start, end)[:-1] for start, end in zip(points, points[1:])]), [points[-1]], axis=0)

def points_linear_interpolation(start: np.ndarray, end: np.ndarray) -> np.ndarray:
    # line returns the pixels of the line described by the 2 points
    # https://scikit-image.org/docs/stable/api/skimage.draw.html#line
    # Nota(tobi): Aca hay una bocha de truquito, lo podemos simplificar
    return np.stack(skimg.draw.line(*start.astype(int), *end.astype(int)), axis=-1)

def interpolate_missing(brightest_point_profile_index: np.ndarray, normal_lines: np.ndarray, prev_frame_points: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
  valid_values = []
  invalid_values = []
  none_flag = False
  left_pos = 0
  previous_index = 0
  interpolation_points: List[Tuple[int, int]] = []
  left_point = Tuple[int, int]
  """
  Si los primeros o ultimos n puntos son None, se descartan
  """
  converted_points = [index_to_point(bp, nl) for bp, nl in zip(brightest_point_profile_index, normal_lines)]
  
  for i, cp in enumerate(converted_points):
    if cp:
      if none_flag:
        interpolation_points.append(cp)
        for j in range(1, 3):
          new_pos = i + j
          if new_pos < len(converted_points) and converted_points[new_pos]:
            interpolation_points.append(converted_points[new_pos])

          #interpolo entre previous_point y next_point, pero elimino lo que me corri, osea saco los primeros l_pos
        interpolation = points_linear_interpolation(np.asarray(left_point), np.asarray(cp))[:]
        print(f'Interpolation between: {left_point} and {cp}')
        print(f'Ans: {interpolation}')
          # print(len(interpolation), len(interpolation))
        valid_values.extend(interpolation)
        invalid_values.extend(interpolation)
          
        none_flag = False
      # else:
      #   # dejo el punto en converted como esta y lo appendeo a los valores validos
      valid_values.append(cp)
    else:
      # no es valido el punto y vengo de uno valido
      if not none_flag:
        # busco el indice del punto mas lejos que tenga para atras
        if len(valid_values) > 0:
          left_pos = min(len(valid_values), 3)
          # print(left_pos, len(valid_values))
          # me guardo ese punto valido como punto izq de la interpolacion
          # interpolation_points.extend(valid_values[-left_pos:])
          left_point = valid_values[-left_pos:]
          #indice previo
          previous_index = i
          none_flag = True
  print(np.array(valid_values))
  print(np.array(invalid_values))
  return np.array(valid_values), np.array(invalid_values)
    
# brightest_point = media y error
def index_to_point(brightest_point: Tuple[float, float], points: np.ndarray) -> Optional[Tuple[float, float]]:
    """
        Obtener las coordenadas de un punto ubicado entre otros dos.
        Si no esta contenido en la lista de puntos se ignora (None)
    """
    idx = brightest_point[0]

    # TODO(tobi): habilitarlo por config 
    if brightest_point[1] > 0.2 or int(idx) < 0 or int(idx) + 1 >= len(points):
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
    f = lambda x, m, s: gaussian(x, m, s) * max_color
    popt, pcov = curve_fit(f, xdata, intensity_profile)
    p_error = np.square(np.diag(pcov))
  
    return popt[0], p_error[0]

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
