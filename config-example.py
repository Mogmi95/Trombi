# -*- coding: utf-8 -*-
"""A basic config file."""

import os


WTF_CSRF_ENABLED = True
SECRET_KEY = 'hello-github'
# Params
DEFAULT_FILE_STORAGE = 'filesystem'
DATABASE_PATH = '/tmp/trombi_database.sqlite'
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + DATABASE_PATH
UPLOADS_FOLDER = os.path.realpath('.') + '/static/photos/'
WEBSITE_URL = 'http://localhost:5000'

DATABASE_PERSONS_FILE = 'data/example-persons.csv'
DATABASE_TEAMS_FILE = 'data/example-teams.csv'
DATABASE_ROOMS_FILE = 'data/example-rooms.csv'

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
