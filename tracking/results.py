import os
from typing import List

from .models import DisplayConfig, Result

from .image_utils import create_film, create_result_zip, get_frame, add_img_to_plot, add_points_to_plot, add_normal_lines, save_plot

# TODO(tobi): Not used. Find use or deprecate. It could be usefull to store point data.
# def save_info_as_json(folder: str, points: List[Point], frame_name: str) -> None:
#     if frame_name == '0':  # json file is not yet created
#         points_dict = {}
#     else:
#         with open(f'{folder}/results/download/positions.json') as json_file:
#             points_dict = json.load(json_file)

#     frame = f'frame_{frame_name}'
#     points_dict[frame] = []
#     for point in points:
#         points_dict[frame].append({'x': point.x, 'y': point.y})

#     f = open(f'{folder}/results/download/positions.json', 'w')
#     f.write(json.dumps(points_dict))
#     f.close()

def save_results(folder: str, results: List[Result], display_conf: DisplayConfig) -> None:
    for result in results:
        save_frame_results(folder, result, display_conf)

    #TODO(nacho para tobi): guardar los results.

def save_frame_results(folder: str, result: Result, display_conf: DisplayConfig) -> None:
    """
        In `folder`/results, save image with points and debug_points,
        as well as the points in a json file
    """

    img, _ = get_frame(result.frame)

    # Make plot
    add_img_to_plot(img)
    add_points_to_plot(result.points, 'tab:blue', display_conf.scatter)
    if display_conf.invalid_values and result.none_points is not None and len(result.none_points) > 0:
      add_points_to_plot(result.none_points, 'tab:red', display_conf.scatter)

    if display_conf.normal_lines and result.normal_lines is not None:
        add_normal_lines(result.normal_lines)

    # Save to results folder
    os.makedirs(f'{folder}/results/download', exist_ok=True)
    frame_name = ''.join(os.path.basename(result.frame).split('.')[:-1])
    save_plot(folder, frame_name)
    # save_info_as_json(folder, points, frame_name)

def save_tracking_film(frames_folder) -> str:
    results_folder = f'{frames_folder}/results'
    create_film(results_folder)
    create_result_zip(results_folder)

    return results_folder
