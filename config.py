# Security
import os

WTF_CSRF_ENABLED = True
SECRET_KEY = 'hello-github'
# Params
DEFAULT_FILE_STORAGE = 'filesystem'
SQLALCHEMY_DATABASE_URI = 'sqlite:////tmp/lol'
UPLOADS_FOLDER = os.path.realpath('.') + '/static/photos/'

DEBUG = True
