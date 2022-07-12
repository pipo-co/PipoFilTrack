import dataclasses
import json
from typing import List, Dict, Type

import numpy as np
from flask import render_template, request, make_response, jsonify, Flask
from werkzeug.exceptions import HTTPException

from tracking.image_utils import frames_iterator
from tracking.main import track_filament
from tracking.models import Config, ApplicationError

app = Flask(
    __name__,
    template_folder='frontend',
    static_folder="static",
    instance_relative_config=True
)
# app.secret_key = 'secret key'

ALLOWED_IMAGE_TYPES: List[str] = ['.tif', '.tiff', '.jpg', '.jpeg', '.avi', '.png']
TYPE_TO_INPUT: Dict[Type, str] = {
    bool:   'checkbox',
    int:    'text',
    float:  'text'
}

@app.after_request
def add_header(response):
    response.headers["Cache-Control"] = "max-age=0, must-revalidate"
    return response

@app.errorhandler(ApplicationError)
def application_error_handler(e):
    return make_response(jsonify(e), 400)

@app.errorhandler(HTTPException)
def application_error_handler(e):
    return make_response(jsonify(ApplicationError(str(e)), e.code))

@app.errorhandler(Exception)
def generic_error_handler(e):
    return make_response(jsonify(ApplicationError(str(e))), 500)

@app.route('/')
def index():
    return render_template(
        'index.html',
        config_fields=dataclasses.fields(Config),
        type2input=TYPE_TO_INPUT,
        allowed_image_types=ALLOWED_IMAGE_TYPES
    )

@app.route('/track', methods=['POST'])
def track():
    if 'points' not in request.form or len(points := json.loads(request.form['points'], object_hook=lambda point: (point['x'], point['y']))) < 2:
        raise ApplicationError('No enough points provided for tracking. At least 2 are required.')

    if 'images[]' not in request.files or len(images := request.files.getlist('images[]')) < 1:
        raise ApplicationError('No images provided for tracking. At least one image is required.')

    config = Config.from_dict(request.form)

    return make_response(jsonify(track_filament(frames_iterator(images, ALLOWED_IMAGE_TYPES), np.array(points), config)))

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
