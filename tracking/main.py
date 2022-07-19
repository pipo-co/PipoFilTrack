from typing import Iterable

import numpy as np
from scipy.special import comb

from .models import Config, TrackingFrameResult, TrackingPoint, TrackingSegment, TrackingResult, TrackingFrameMetadata, TrackingPointStatus
from .tracking import interpolate_missing, gauss_fitting, generate_normal_line_bounds, multi_point_linear_interpolation, points_linear_interpolation


def track_filament(frames: Iterable[np.ndarray], user_points: np.ndarray, config: Config) -> TrackingResult:
    results = []

    prev_frame_points = multi_point_linear_interpolation(user_points)

    for frame in frames:
        # interpolated_points = multi_point_linear_interpolation(prev_frame_points)
        if len(prev_frame_points) < config.max_tangent_length/2:
            break

        normal_lines_limits = generate_normal_line_bounds(prev_frame_points, config.max_tangent_length, config.normal_line_length)
        # No es un ndarray porque no todas salen con la misma longitud
        normal_lines = [points_linear_interpolation(start, end) for start, end in normal_lines_limits]

        intensity_profiles = map(lambda nl, img=frame: read_line_from_img(img, nl), normal_lines)

        brightest_point_profile_index = list(map(lambda ip, img=frame: gauss_fitting(ip, img.max()), intensity_profiles))
        # La media (el punto mas alto) esta en el intervalo (0, len(profile)). 
        # Hay que encontrar las coordenadas del punto que representa la media.
        brightest_point, none_points = interpolate_missing(brightest_point_profile_index, normal_lines, config.cov_threshold)
        # brightest_point, none_points = [index_to_point(idx, nl, pfp) for idx, nl, pfp in zip(brightest_point_profile_index, normal_lines, prev_frame_points)]
        smooth_points = brightest_point

        if config.bezier_smoothing:
            smooth_points = bezier_fitting(brightest_point)

        prev_frame_points = smooth_points

        # TODO: No queremos perder el orden de los puntos. Tenemos que ver la manera de ir clasificando puntos sin perder su orden en la lista.
        #   Esta solucion es temporal
        #   Nos tenemos que sentar a pensar bien como es el modelo de la respuesta, porque no es sencillo
        results.append(TrackingFrameResult(
            TrackingPoint.from_arrays([(prev_frame_points, None)]),
            TrackingFrameMetadata(TrackingSegment.from_arrays(normal_lines_limits))
        ))

    return TrackingResult(results)

# indices (n, 2) de la forma (x, y)
def read_line_from_img(img: np.ndarray, indices: np.ndarray) -> np.ndarray:
    return img[indices[:,1], indices[:,0]]

def bezier_fitting(points: np.ndarray):
    count = points.shape[0]
    idx = np.arange(count).reshape((-1, 1))  # We make it of shape (count, 1) so it can later be broadcast to 2

    n = count - 1
    ts = np.linspace(0, 1, num=count)

    ret = np.zeros((count, 2))
    for i, t in enumerate(ts):
        # Sum of points multiplied by the corresponding Bernstein polynomial
        ret[i, :] = np.sum(points*comb(n, idx)*(t**idx)*((1 - t)**(n - idx)), axis=0)

    return ret
