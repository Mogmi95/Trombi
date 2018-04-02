# -*- coding: utf-8 -*-
"""A basic config file."""

import os


WTF_CSRF_ENABLED = True
SECRET_KEY = 'hello-github'
# Params
DEFAULT_FILE_STORAGE = 'filesystem'
DATABASE_PATH = '/tmp/trombi_database.sqlite'
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + DATABASE_PATH
PHOTOS_FOLDER = os.path.realpath('.') + '/photos/'
CSV_FOLDER = os.path.realpath('.') + '/data/'
WEBSITE_URL = 'http://localhost:5000'
PORT = 5000

# DATABASE SAVES
DATABASE_SAVES_DIRECTORY = os.path.realpath('.') + '/backups'

# Admin credentials
ADMIN_LOGIN = 'admin'
ADMIN_PASSWORD = 'pizza'

# Available languages
LANGUAGES = {
    'en': 'English',
    'fr': 'Français',
}

DEBUG = True