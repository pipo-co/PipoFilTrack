from typing import List, Optional, Tuple

import numpy as np
import skimage as skimg
from scipy import stats
from scipy.optimize import curve_fit
from scipy.special import comb

PIXEL_POINT_RATIO = 1

def multi_point_linear_interpolation(points: np.ndarray, density: int = 1) -> np.ndarray:
    """
    Given a point vector, interpolates linearly between each point pair.
    """
    return np.append(np.concatenate([points_linear_interpolation(start, end)[:-1][::density] for start, end in zip(points, points[1:])]), [points[-1]], axis=0)

def points_linear_interpolation(start: np.ndarray, end: np.ndarray) -> np.ndarray:
    # line returns the pixels of the line described by the 2 points
    # https://scikit-image.org/docs/stable/api/skimage.draw.html#line
    return np.stack(skimg.draw.line(*start.astype(int), *end.astype(int)), axis=-1)

def project_to_line(point: Tuple[float, float], m1: float, b1: float) -> Tuple[float, float]:
    if m1 == 0:
        # Proyección a línea horizontal
        return point[0], b1
    m2 = -1 / m1
    b2 = point[1] - m2 * point[0]
    x = (b2 - b1) / (m1 - m2)
    y = m1*x + b1
    return x, y

def interpolate_points(interpolation_points: List[Tuple[float, float]], none_points: int, leftmost_point: Tuple[float, float], rightmost_point: Tuple[float, float]) -> np.ndarray:
    interpolation_points = np.asarray(interpolation_points)
    try:
        res = stats.linregress(interpolation_points)
    except ValueError:
        return np.asarray([interpolation_points[0] for _ in range(none_points)])

    first_point = project_to_line(leftmost_point, res.slope, res.intercept)
    last_point = project_to_line(rightmost_point, res.slope, res.intercept)

    xs = np.linspace(first_point[0], last_point[0], none_points + 2, endpoint=True)[1:-1]
    points = np.repeat(xs[:, None], 2, axis=1)
    points[:, 1] = points[:, 1] * res.slope + res.intercept

    return points

def interpolate_missing(points: List[Optional[Tuple[float, float]]], previous_points: np.ndarray, inter_len: int) -> Tuple[np.ndarray, List[int], List[int]]:
    """
        Returns results with interpolated points included, or previous points if interpolation couldn't be done.
        Also, a list of the indices of the interpolated/preserved points is provided.
    """
    valid_points: List[Tuple[float, float]] = []
    interpolated_points_idx: List[int]      = []
    preserved_points_idx: List[int]         = []
    initial_to_be_preserved                 = 0

    none_flag = False
    previous_index = 0
    interpolation_points: List[Tuple[float, float]] = []
    leftmost_point: Tuple[float, float]
    rightmost_point: Tuple[float, float]

    for i, point in enumerate(points):
        if point:
            if none_flag:
                if i + 1 != len(points) and not (i + 1 < len(points) and points[i + 1]):
                    continue

                interpolation_points.append(point)
                rightmost_point = point
                for j in range(1, inter_len):
                    new_pos = i + j
                    if new_pos < len(points) and points[new_pos]:
                        interpolation_points.append(points[new_pos])

                # interpolo entre previous_point y next_point, pero elimino lo que me corri, osea saco los primeros l_pos
                point_amount = i - previous_index - 1
                interpolation = interpolate_points(interpolation_points, point_amount, leftmost_point, rightmost_point)

                valid_points.extend(interpolation)
                interpolated_points_idx.extend(range(previous_index + 1, i))  # Le agregamos los indices de los puntos interpolados
                interpolation_points = []
                none_flag = False
            # else:
            #   # dejo el punto en converted como esta y lo appendeo a los valores validos
            valid_points.append(point)
        else:
            # no es valido el punto y vengo de uno valido
            if not none_flag:
                # busco el indice del punto mas lejos que tenga para atras
                if len(valid_points) > 0:
                    left_pos = min(len(valid_points), inter_len)

                    interpolation_points.extend(valid_points[-left_pos:])
                    leftmost_point = interpolation_points[-1]
                    # indice previo
                    previous_index = i - 1
                    none_flag = True
                else:
                    initial_to_be_preserved += 1

    # Calculamos los puntos que no pudimos interpolar al principio y les asignamos el punto previo (los "preservamos")
    if initial_to_be_preserved > 0:
        valid_points = list(previous_points[:initial_to_be_preserved]) + valid_points
        preserved_points_idx.extend(range(initial_to_be_preserved))

    # Lo mismo pero al final
    points_count = len(points)
    valid_count = len(valid_points)
    if points_count - valid_count > 0:
        valid_points.extend(previous_points[valid_count:])
        preserved_points_idx.extend(range(valid_count, points_count))

    return np.array(valid_points), interpolated_points_idx, preserved_points_idx

def profile_pos_to_point(pos: float, points: np.ndarray) -> Optional[Tuple[float, float]]:
    """
    A partir de una lista de puntos que representan el segmento de una recta, y una posicion (1D) dentro de esa recta,
    se obtiene el punto en 2D de dicha posicion.
    En caso de que la posicion no se encuentre en la recta, se retorna None.
    """
    if int(pos) < 0 or int(pos) + 1 >= len(points):
        return None

    start   = points[int(pos)]
    end     = points[int(pos)+1]
    delta   = pos - int(pos)

    new_x = start[0] + delta * (end[0] - start[0])
    new_y = start[1] + delta * (end[1] - start[1])

    return new_x, new_y

def gauss_fitting(intensity_profile: np.ndarray, max_color: int, max_error: float, offset: bool) -> Optional[float]:
    """
    Ajusta los puntos a una distribucion gaussiana y retorna su maximo (la media) y su error.
    """
    profile_len = len(intensity_profile)
    xdata = np.arange(profile_len)
    try:
        popt, pcov = curve_fit(
            (lambda x, mu, sig, a, y0: y0 + (a-y0)*np.exp(-((x-mu)**2)/(2.*sig**2.))) if offset else
            (lambda x, mu, sig: max_color*(1./(np.sqrt(2.*np.pi)*sig)*np.exp(-np.power((x - mu)/sig, 2.)/2))),
            xdata,
            intensity_profile,
            p0=([profile_len/2, 1, max_color/2, max_color/2]) if offset else ([profile_len/2, 1]),
        )
        p_error = np.square(np.diag(pcov))
        return popt[0] if p_error[0] < max_error else None
    except RuntimeError:
        # Intensity profile failed to be fitted by a gaussian curve
        return None

def generate_normal_line_bounds(points: np.ndarray, tangent_length: int, normal_len: float) -> np.ndarray:
    d = tangent_length

    start = points[:-d]
    end = points[d:]

    tangent_angle = np.arctan2(end[:,1] - start[:,1], end[:,0] - start[:,0])
    
    normal_angle = np.zeros(len(points))
    normal_angle[d//2:-d//2] = tangent_angle + np.pi/2
    normal_angle[:d//2] = normal_angle[d//2]
    normal_angle[-d//2:] = normal_angle[-d//2 - 1]

    # Seno y coseno de la normal. Usados para generar los limites de la misma 
    component_multiplier = np.stack((np.cos(normal_angle), np.sin(normal_angle)), axis=1)
    upper = points + component_multiplier * normal_len / 2
    lower = points - component_multiplier * normal_len / 2

    bounds = np.stack((upper, lower), axis=1)

    return np.rint(bounds).astype(np.int64)

# indices (n, 2) de la forma (x, y)
def read_line_from_img(img: np.ndarray, ind: np.ndarray) -> np.ndarray:
    indices = ind[(ind[:,0] > 0) & (ind[:,0] < img.shape[1]) & (ind[:,1] > 0) & (ind[:,1] < img.shape[0])]
    return img[indices[:,1], indices[:,0]]

def bezier_fitting(points: np.ndarray, segment_len: int):
    if np.isinf(comb(segment_len, segment_len // 2)):
        raise ValueError('Bezier segment is too long. Try lowering it\'s length')

    total_points = len(points)
    bezier_segments = [points[i: i + segment_len] for i in range(0, total_points, segment_len-1)]
    total_segments = len(bezier_segments)
    ret = np.zeros((total_points, 2))

    for seg_idx, segment in enumerate(bezier_segments):
        # How many points we want from the bezier curve
        # It could be a parameter, but we always want the same amount of points as the input
        count = len(segment)

        size = count
        n = size - 1

        idx = np.arange(size).reshape((-1, 1))  # We make it of shape (count, 1) so it can later be broadcast to 2
        ts = np.linspace(0, 1, num=count-1 if seg_idx < total_segments-1 else count)  # Queremos que sea abierto a derecha, excepto en el ultimo caso

        for i, t in enumerate(ts):
            # Sum of points multiplied by the corresponding Bernstein polynomial
            #TODO(tobi): Se podria calcular solo una vez el polinomio para el caso segment_len
            ret[seg_idx*(segment_len-1) + i, :] = np.sum(segment * comb(n, idx) * (t**idx) * ((1 - t)**(n - idx)), axis=0)

    return ret
