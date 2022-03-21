from flask import Flask

UPLOAD_FOLDER = 'static/uploads/'

server = Flask(__name__, template_folder='frontend')
server.secret_key = 'secret key'
server.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
