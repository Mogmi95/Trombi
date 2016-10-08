# Security
import os

WTF_CSRF_ENABLED = True
SECRET_KEY = 'hello-github'
# Params
DEFAULT_FILE_STORAGE = 'filesystem'
SQLALCHEMY_DATABASE_URI = 'sqlite:////tmp/lol'
UPLOADS_FOLDER = os.path.realpath('.') + '/static/photos/'

DATABASE_PERSONS_DEFAULT_FILE = 'data/default_persons.csv'
DATABASE_TEAMS_DEFAULT_FILE = 'data/default_teams.csv'
DATABASE_ROOMS_DEFAULT_FILE = 'data/default_rooms.csv'
DATABASE_PERSONS_FILE = 'data/persons.csv'
DATABASE_TEAMS_FILE = 'data/teams.csv'
DATABASE_ROOMS_FILE = 'data/rooms.csv'

DEBUG = True
