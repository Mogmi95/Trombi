"""The application."""
from flask.ext.sqlalchemy import SQLAlchemy
import flask
import flask.ext.sqlalchemy

# Create the Flask application and the Flask-SQLAlchemy object.
app = flask.Flask(__name__, static_url_path='/static')
app.config.from_object('config')
db = SQLAlchemy(app)
