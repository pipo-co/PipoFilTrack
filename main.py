import dataclasses
import json
import os

import numpy as np
from flask import render_template, request, make_response, jsonify, Flask
from werkzeug.exceptions import HTTPException

from tracking.image_utils import frames_iterator
from tracking.main import track_filament
from tracking.models import Config, ApplicationError

app = Flask(__name__, instance_relative_config=True)
app.secret_key = os.getenv('SECRET_KEY')

ALLOWED_IMAGE_TYPES = ['.tif', '.tiff', '.jpg', '.jpeg', '.png']

@app.after_request
def add_header(response):
    response.headers["Cache-Control"] = "max-age=0, must-revalidate"
    return response

@app.errorhandler(ApplicationError)
def application_error_handler(e):
    return make_response(jsonify(e), 400)

@app.errorhandler(HTTPException)
def http_exception_handler(e):
    return make_response(jsonify(ApplicationError(str(e)), e.code))

@app.errorhandler(Exception)
def generic_error_handler(e):
    return make_response(jsonify(ApplicationError(str(e))), 500)

@app.route('/')
def index():
    return render_template(
        'index.html',
        config_fields=dataclasses.fields(Config),
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

@app.route('/health', methods=['GET'])
def health():
    return "Healthy: OK"

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
