import json
from typing import List

import numpy as np
from flask import render_template, request, make_response, jsonify, Flask

from tracking.image_utils import frames_iterator
from tracking.main import TrackStep, track_filament
from tracking.models import Config, ApplicationError

ALLOWED_IMAGE_EXT: List[str] = ['.tif', '.tiff', '.jpg', '.jpeg', '.avi', '.png']

app = Flask(
    __name__,
    template_folder='frontend',
    static_folder="static",
    instance_relative_config=True
)
# app.secret_key = 'secret key'

@app.after_request
def add_header(response):
    response.headers["Cache-Control"] = "max-age=0, must-revalidate"
    return response

@app.route('/')
def index():
    return render_template('index.html', steps=TrackStep.values())

@app.route('/track', methods=['POST'])
def track():
    if 'points' not in request.form or len(points := json.loads(request.form['points'], object_hook=lambda point: (point['x'], point['y']))) < 2:
        return make_response(jsonify(ApplicationError('No enough points provided for tracking. At least 2 are required.')), 400)

    if 'images[]' not in request.files or len(images := request.files.getlist('images[]')) < 1:
        return make_response(jsonify(ApplicationError('No images provided for tracking. At least one image is required.')), 400)

    # TODO(tobi): Recibirlo
    config = Config(
        smooth_y=False,
        smooth_x=False,
        cov_threshold=0.1,
        moving_average_count=15,
        max_tangent_length=15,
        normal_line_length=10,
    )

    try:
        return make_response(jsonify(track_filament(frames_iterator(images, ALLOWED_IMAGE_EXT), np.array(points), config)))
    except ApplicationError as e:
        return make_response(jsonify(e), 400)
    except Exception as e:
        return make_response(jsonify(ApplicationError(str(e))), 500)

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
