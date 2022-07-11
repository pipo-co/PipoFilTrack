from typing import Iterable

import numpy as np

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

        if config.smooth_x:
            smooth_points[:, 0] = moving_average(brightest_point[:, 0], config.moving_average_count)

        if config.smooth_y:
            smooth_points[:, 1] = moving_average(brightest_point[:, 1], config.moving_average_count)

        prev_frame_points = smooth_points

        # TODO: No queremos perder el orden de los puntos. Tenemos que ver la manera de ir clasificando puntos sin perder su orden en la lista.
        #   Esta solucion es temporal
        #   Nos tenemos que sentar a pensar bien como es el modelo de la respuesta, porque no es sencillo
        results.append(TrackingFrameResult(
            TrackingPoint.from_arrays([(brightest_point, None), (none_points, TrackingPointStatus.INTERPOLATED)]),
            TrackingFrameMetadata(TrackingSegment.from_arrays(normal_lines_limits))
        ))

    return TrackingResult(results)

# indices (n, 2) de la forma (x, y)
def read_line_from_img(img: np.ndarray, indices: np.ndarray) -> np.ndarray:
    return img[indices[:,1], indices[:,0]]

def moving_average(values: np.ndarray, N: int) -> np.ndarray:
    extended = np.append(np.repeat(values[0], N//2), values)
    extended = np.append(extended, np.repeat(values[-1], N//2))
    return np.correlate(extended, np.ones(N)/N, mode='valid')
