import json
import os
import re
from enum import Enum
from typing import List, Optional

import numpy as np
import skimage as skimg

import tracking.image_utils as image_utils
from tracking.tracking import adjust_points
from tracking.types_utils import Point

SAMPLE_POINTS = 100
PIXEL_POINT_RATIO = 1

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

def points_linear_interpolation(points: np.ndarray, pixel_point_ratio: int) -> np.ndarray:
    """
    Given a point vector, interpolates linearly between each point pair.
    """
    # line returns the pixels of the line described by the 2 points
    # https://scikit-image.org/docs/stable/api/skimage.draw.html#line
    # Nota(tobi): Aca hay una bocha de truquito, lo podemos simplificar
    return np.concatenate([np.stack(skimg.draw.line(*start, *end), axis=-1) for start, end in zip(points, points[1:])])

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

    starting_points = points_linear_interpolation(user_points, PIXEL_POINT_RATIO)
    if up_to_step == TrackStep.INTERPOLATION:
        save_results(frames_folder, img, starting_points, start_frame, scatter=True)
        return

    # TODO(tobi): Que normal_len sea un parametro, y que sino se pueda calcular a partir del ancho del tubo en esa seccion
    normal_len = 10
    normal_line_resolution = 15
    normal_lines = None
    scatter = up_to_step != TrackStep.NORMAL
    prev_frame_points = starting_points

    for i, frame in enumerate(frames):
        img, _ = image_utils.get_frame(frame, invert)
        blurred_img = image_utils.blur_img(img)

        if up_to_step == TrackStep.FILTER:
            img = blurred_img
            prev_frame_points = None
        elif up_to_step == TrackStep.NORMAL:
            normal_lines = generate_normal_line_bounds(prev_frame_points, normal_line_resolution, normal_len)

        elif up_to_step == TrackStep.ALL:
            prev_frame_points = adjust_points(blurred_img, prev_frame_points, normal_len)

        save_results(frames_folder, img, prev_frame_points, frame, normal_lines=normal_lines,scatter=scatter)


def generate_normal_line_bounds(points: np.ndarray, resolution: int, line_len: float) -> np.ndarray:
    
    d = resolution

    start = points[:-d]
    end = points[d:]

    section_angle = np.arctan2(end[:,1] - start[:,1], end[:,0] - start[:,0])
    
    normal_angle = np.zeros(len(points))
    normal_angle[d//2:-d//2] = section_angle + np.pi/2
    normal_angle[:d//2] = normal_angle[d//2]
    normal_angle[-d//2:] = normal_angle[-d//2 -1]

    component_multiplier = np.stack((np.cos(normal_angle), np.sin(normal_angle)), axis=1)
    upper = points + component_multiplier * line_len / 2
    lower = points - component_multiplier * line_len / 2
    
    bounds = np.stack((upper, lower), axis=1)

    return np.rint(bounds).astype(np.int64)

def save_tracking_film(frames_folder) -> str:
    results_folder = f'{frames_folder}/results'
    image_utils.create_film(results_folder)
    image_utils.create_result_zip(results_folder)

    return results_folder
