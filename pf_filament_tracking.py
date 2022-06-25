import glob
import json
import os
import shutil
import time
import traceback

import numpy as np
from flask import (flash, redirect, render_template, request,
                   send_from_directory)
from flask_apscheduler import APScheduler
from werkzeug.utils import secure_filename

from __init__ import server
from tracking.files import get_frame_identifiers
from tracking.image_utils import (check_is_multitiff, convert_avi_to_tif,
                                  convert_jpg_to_tif, save_first_frame_as_jpg)
from tracking.main import TrackStep, track_filament
from tracking.models import Config, DisplayConfig
from tracking.results import save_results, save_tracking_film


@server.after_request
def add_header(response):
    response.headers["Cache-Control"] = "max-age=0, must-revalidate"
    return response


@server.route('/')
def index():
    return render_template('upload.html')


@server.route('/', methods=['POST'])
def upload_images():
    if 'files[]' not in request.files:
        flash('No file part')
        return redirect(request.url)

    server_folder = '/'.join([server.config['UPLOAD_FOLDER'][:-1], str(round(time.time()*1000000.0))])
    os.makedirs(server_folder, exist_ok=True)
    files = request.files.getlist('files[]')

    if len(files) == 0:
        flash('Debe seleccionar al menos una imagen')
        return redirect(request.url)

    original = None

    for curr_index, file in enumerate(files):
        extension = os.path.splitext(file.filename)[1].lower()

        filename = secure_filename(str(curr_index) + extension)
        complete_filename = '/'.join([server_folder, filename])
        file.save(complete_filename)

        if curr_index == 0:
            original, filtered, img_shape = save_first_frame_as_jpg(server_folder, filename, complete_filename)

        if extension == ".tiff" or extension == ".tif":
            check_is_multitiff(server_folder, complete_filename, extension)
        elif extension == ".jpg" or extension == '.jpeg':
            convert_jpg_to_tif(complete_filename)
        elif extension == '.avi':
            convert_avi_to_tif(server_folder, complete_filename)

    return render_template('selection.html', original=original, filtered=filtered, img_width=img_shape[1], img_height=img_shape[0], steps=TrackStep.values())


@server.route('/track', methods=['POST'])
def track():
    points = json.loads(request.form['points'], object_hook=lambda point: (point['x'], point['y']))
    folder = os.path.dirname(request.form['filename'])
    up_to_step = TrackStep.from_str(request.form['up_to_step'])
    try:
        frames = get_frame_identifiers(folder)
        r = track_filament(frames, np.array(points), Config(smooth_y=False, smooth_x=False, moving_average_count=15, max_tangent_length=15, normal_line_length=10, up_to_step=up_to_step))
        save_results(folder, r, DisplayConfig(scatter=True, normal_lines=up_to_step == TrackStep.NORMAL))
        results_folder = save_tracking_film(folder)
    except Exception as e:
        flash(str(e))
        traceback.print_exc()
        return render_template('upload.html', filename=request.form['filename'], ratio=0.9) #TODO(nacho): hay que sacar el ratio de la imagen (width/heigth)
    results = sorted(glob.glob(f'{results_folder}/*.png'), key=os.path.getmtime)
    return render_template('result.html', results=results, results_folder=results_folder)


@server.route('/download_result', methods=['POST'])
def download_result():
    results_folder = request.form['results_folder']
    delete_file = f'{results_folder}/delete'
    if not os.path.exists(delete_file):
        f = open(delete_file, 'x')
        f.close()
    return send_from_directory(results_folder, filename='results.zip', as_attachment=True)


def delete_uploaded_folders():
    folders = glob.glob(server.config['UPLOAD_FOLDER'] + '*')

    for folder in folders:
        delete = f'{folder}/results/delete'
        if os.path.exists(delete):
            # Age of delete file in seconds
            age = time.time() - os.path.getctime(delete)
            if age > 10800:  # (3 hours)
                shutil.rmtree(folder)
        elif (time.time() - os.path.getctime(folder)) > 86400:  # (1 day)
            # The tracking process may have gotten interrupted so the delete file was never created,
            # then, if the folder was created more than three hours ago, we assume we can delete it
            shutil.rmtree(folder)

if __name__ == '__main__':
    scheduler = APScheduler()
    scheduler.add_job(id='Scheduled Delete Task', func=delete_uploaded_folders, trigger='interval', seconds=3600)
    scheduler.start()
    delete_uploaded_folders()
    server.run(host='0.0.0.0', debug=True, use_reloader=False)
