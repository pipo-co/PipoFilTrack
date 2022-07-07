
from typing import List

import numpy as np

from .models import Config, Result, TrackStep
from .image_utils import get_frame 
from .tracking import interpolate_missing, gauss_fitting, generate_normal_line_bounds, multi_point_linear_interpolation, points_linear_interpolation


def track_filament(frames: List[str], user_points: np.ndarray, config: Config) -> List[Result]:
    """
        Given a folder with images and a set of points, tracks a 
         filament containing those points in all the images (or frames)
    """

    start_frame = frames[0]
    img, invert = get_frame(start_frame)
    prev_frame_points = multi_point_linear_interpolation(user_points)
    results = []

    if config.up_to_step == TrackStep.INTERPOLATION:
        return [Result(prev_frame_points, None, start_frame, None)]


    for frame in frames:
        img, _ = get_frame(frame, invert)
        
        # interpolated_points = multi_point_linear_interpolation(prev_frame_points)

        normal_lines_limits = generate_normal_line_bounds(prev_frame_points, config.max_tangent_length, config.normal_line_length)

        # No es un ndarray porque no todas salen con la misma longitud
        normal_lines = [points_linear_interpolation(start, end) for start, end in normal_lines_limits]
        
        intensity_profiles = map(lambda nl, img=img: read_line_from_img(img, nl), normal_lines)
        
        brightest_point_profile_index = map(lambda ip, img=img: gauss_fitting(ip, img.max()), intensity_profiles)
        # La media (el punto mas alto) esta en el intervalo (0, len(profile)). 
        # Hay que encontrar las coordenadas del punto que representa la media.
        brightest_point, none_points = interpolate_missing(brightest_point_profile_index, normal_lines, prev_frame_points)
        # brightest_point, none_points = [index_to_point(idx, nl, pfp) for idx, nl, pfp in zip(brightest_point_profile_index, normal_lines, prev_frame_points)]
        smooth_points = brightest_point

        if config.smooth_x:
            smooth_points[:, 0] = moving_average(brightest_point[:, 0], config.moving_average_count)
        
        if config.smooth_y:
            smooth_points[:, 1] = moving_average(brightest_point[:, 1], config.moving_average_count)

        prev_frame_points = smooth_points
        results.append(Result(brightest_point, none_points, frame, normal_lines_limits))
    
    return results

# indices (n, 2) de la forma (x, y)
def read_line_from_img(img: np.ndarray, indices: np.ndarray) -> np.ndarray:
    return img[indices[:,1], indices[:,0]]

def moving_average(values: np.ndarray, N: int) -> np.ndarray:
    extended = np.append(np.repeat(values[0], N//2), values)
    extended = np.append(extended, np.repeat(values[-1], N//2))
    return np.correlate(extended, np.ones(N)/N, mode='valid')