import json
import os
import re
from typing import List

import numpy as np

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

def save_results(folder, img, points: np.ndarray, frame: str, scatter: bool = False) -> None:
    """
        In `folder`/results, save image with points and debug_points,
        as well as the points in a json file
    """

    # Make plot
    image_utils.add_img_to_plot(img)
    image_utils.add_points_to_plot(points, 'tab:blue', scatter)

    # Save to results folder
    os.makedirs(f'{folder}/results/download', exist_ok=True)
    frame_name = ''.join(os.path.basename(frame).split('.')[:-1])
    image_utils.save_plot(folder, frame_name)
    # save_info_as_json(folder, points, frame_name)

def points_linear_interpolation(points: np.ndarray, pixel_point_ratio: int) -> np.ndarray:
    """
    Given a point vector, interpolates linearly between each point pair adding a point every `pixel_point_ratio` pixels.
    """
    ret = []
    for start, end in zip(points, points[1:]):
        ratio = int(np.linalg.norm(start - end, ord=2)) // pixel_point_ratio + 1
        x = np.linspace(start[0], end[0], ratio).round().astype(np.uint8)
        y = np.linspace(start[1], end[1], ratio).round().astype(np.uint8)
        ret.append(np.stack((x, y), axis=-1))

    return np.unique(np.concatenate(ret), axis=0)

def track_filament(frames_folder: str, user_points: np.ndarray) -> str:
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
    img_gauss = image_utils.gauss_img(img)

    starting_points = points_linear_interpolation(user_points, PIXEL_POINT_RATIO)
    # # start_angle = get_line_angle(start_point, end_point)

    # Descomentar para mostrar la interpolacion
    # save_results(frames_folder, img, points, [], start_frame)

    # TODO(tobi): Que normal_len sea un parametro, y que sino se pueda calcular a partir del ancho del tubo en esa seccion
    normal_len = 10

    prev_frame_points = starting_points
    for i, frame in enumerate(frames):
        img, _ = image_utils.get_frame(frame, invert)
        blurred_img = image_utils.blur_img(img)

        prev_frame_points = adjust_points(blurred_img, prev_frame_points, normal_len)
        # prev_frame_points = smooth(prev_frame_points)

        save_results(frames_folder, img, prev_frame_points, frame, scatter=True)

    results_folder = f'{frames_folder}/results'
    image_utils.create_film(results_folder)
    image_utils.create_result_zip(results_folder)

    return results_folder
