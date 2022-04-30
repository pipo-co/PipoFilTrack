import json
import os
import re
from typing import List, Tuple

import numpy as np

# Project imports
import tracking.image_utils as image_utils
from tracking.tracking import (adjust_points, get_line_angle, outline_filament,
                               smooth)
from tracking.types_utils import Conf, Point

SAMPLE_POINTS = 100
SEGMENT_POINT_RATIO = 1

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


def save_results(folder, img, points: np.ndarray, debug_points: List[Point], frame: str) -> None:
    """
        In `folder`/results, save image with points and debug_points,
        as well as the points in a json file
    """

    # Make plot
    image_utils.add_img_to_plot(img)
    if debug_points is not None and len(debug_points) > 0:
        from itertools import groupby, zip_longest
        i = (list(g) for _, g in groupby(debug_points, key=debug_points[0].__ne__))
        debug_points_list = [a + b for a, b in zip_longest(i, i, fillvalue=[])]
        # image_utils.add_points_to_plot(debug_points, 'red')
        for debug_pts in debug_points_list:
            image_utils.add_points_to_plot(debug_pts, 'darkgrey')
    image_utils.add_points_to_plot(points, 'tab:blue')

    # Save to results folder
    os.makedirs(f'{folder}/results/download', exist_ok=True)
    frame_name = ''.join(os.path.basename(frame).split('.')[:-1])
    image_utils.save_plot(folder, frame_name)
    # save_info_as_json(folder, points, frame_name)


def track_filament(frames_folder: str, canvas_shape: Tuple[int, int], points: np.ndarray) -> str:
    """
        Given a folder with images and a set of points, tracks a 
         filament containing those points in all the images (or frames)
    """
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
    
    points = points / canvas_shape * np.flip(img.shape)

    interpol = []

    for start, end in zip(points, points[1:]):
        ratio = int(np.linalg.norm(start-end)) // SEGMENT_POINT_RATIO
        x = np.linspace(start[0], end[0], ratio).round().astype(np.uint8)
        y = np.linspace(start[1], end[1], ratio).round().astype(np.uint8)
        interpol.append(np.array((x, y)))

    interpol = np.concatenate(interpol, axis=1)
    # # start_angle = get_line_angle(start_point, end_point)

    # step_size = 3
    # points, debug_points, filament_width = outline_filament(Conf(
    #     start=start_point,
    #     current_position=start_point,
    #     end=end_point,
    #     start_angle=start_angle,
    #     max_step_size=step_size,
    #     angle_aperture=math.pi,
    #     angles_amount=100,
    #     img=img_gauss
    # ))
    # if len(points) < 2:
    #     raise Exception('Tracking failed, please try again')

    # points = smooth(points)
    
    save_results(frames_folder, img, interpol, [], start_frame)
    # save_results(frames_folder, img_gauss, points, debug_points, start_frame)

    # print(f'\nAdjusting points to frame number ', end='')
    next_frames = frames[1:]  # start_frame skipped, already analyzed (it's the base for the adjusting)
    prev_frame_points = points
    for i, frame in enumerate(next_frames):
        img, _ = image_utils.get_frame(frame, invert)
        blurred_img = image_utils.blur_img(img)

        prev_frame_points, debug_points = adjust_points(blurred_img, prev_frame_points, filament_width)
        # prev_frame_points = smooth(prev_frame_points)

        save_results(frames_folder, img, prev_frame_points, [], frame)
        # save_results(frames_folder, img, prev_frame_points, debug_points, frame)

    results_folder = f'{frames_folder}/results'
    image_utils.create_film(results_folder)
    image_utils.create_result_zip(results_folder)

    return results_folder
