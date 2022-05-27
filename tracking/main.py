import json
import os
import re
from enum import Enum
from typing import List, Optional

import numpy as np

import tracking.image_utils as image_utils
from tracking.tracking import adjust_points, multi_point_linear_interpolation
from tracking.types_utils import Point

SAMPLE_POINTS = 100

# TODO(tobi): Not used. Find use or deprecate. It could be usefull to store point data.
def save_info_as_json(folder: str, points: List[Point], frame_name: str) -> None:
    if frame_name == '0':  # json file is not yet created
        points_dict = {}
    else:
        with open(f'{folder}/results/download/positions.json') as json_file:
            points_dict = json.load(json_file)

    frame = f'frame_{frame_name}'
    points_dict[frame] = []
    for point in points:
        points_dict[frame].append({'x': point.x, 'y': point.y})

    f = open(f'{folder}/results/download/positions.json', 'w')
    f.write(json.dumps(points_dict))
    f.close()

def save_results(folder, img, points: np.ndarray, frame: str, normal_lines: Optional[np.ndarray] = None, scatter: bool = False) -> None:
    """
        In `folder`/results, save image with points and debug_points,
        as well as the points in a json file
    """

    # Make plot
    image_utils.add_img_to_plot(img)
    image_utils.add_points_to_plot(points, 'tab:blue', scatter)

    if normal_lines is not None:
        image_utils.add_normal_lines(normal_lines)

    # Save to results folder
    os.makedirs(f'{folder}/results/download', exist_ok=True)
    frame_name = ''.join(os.path.basename(frame).split('.')[:-1])
    image_utils.save_plot(folder, frame_name)
    # save_info_as_json(folder, points, frame_name)


class TrackStep(Enum):
    INTERPOLATION   = "interpolation"
    FILTER          = "filter"
    NORMAL          = "normal"
    ALL             = "all"

    @classmethod
    def values(cls):
        return list(map(lambda c: c.value, cls))

    @classmethod
    def from_str(cls, val):
        if val not in cls.values():
            raise ValueError(f'"{val}" is not a supported track step')
        return cls(val)

def track_filament(frames_folder: str, user_points: np.ndarray, up_to_step: TrackStep = TrackStep.ALL) -> None:
    """
        Given a folder with images and a set of points, tracks a 
         filament containing those points in all the images (or frames)
    """

    # TODO(tobi): File system manipulation should go in another module. At least a private function
    frames = []
    for root, _, filenames in os.walk(frames_folder):
        if 'results' in root:
            continue
        for filename in sorted(filenames, key=lambda x: int(re.search(r'\d+', x).group())):
            if filename.endswith('.tif'):
                frames.append(os.path.join(root, filename))

    start_frame = frames[0]
    img, invert = image_utils.get_frame(start_frame)

    if up_to_step == TrackStep.INTERPOLATION:
        save_results(frames_folder, img, multi_point_linear_interpolation(user_points), start_frame, scatter=True)
        return

    # TODO(tobi): Que normal_len sea un parametro, y que sino se pueda calcular a partir del ancho del tubo en esa seccion
    normal_len = 10
    angle_resolution = 15
    normal_lines_bounds = None
    scatter = up_to_step != TrackStep.NORMAL
    prev_frame_points = user_points

    for i, frame in enumerate(frames):
        img, _ = image_utils.get_frame(frame, invert)
        blurred_img = image_utils.blur_img(img)

        if up_to_step == TrackStep.FILTER:
            img = blurred_img
            prev_frame_points = None

        elif up_to_step == TrackStep.ALL:
            interpolated_points = multi_point_linear_interpolation(prev_frame_points)
            prev_frame_points, normal_lines_bounds = adjust_points(img, interpolated_points, normal_len, angle_resolution)

        save_results(frames_folder, img, prev_frame_points, frame, normal_lines=normal_lines_bounds, scatter=scatter)

def save_tracking_film(frames_folder) -> str:
    results_folder = f'{frames_folder}/results'
    image_utils.create_film(results_folder)
    image_utils.create_result_zip(results_folder)

    return results_folder
