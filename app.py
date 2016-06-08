from flask.ext.sqlalchemy import SQLAlchemy
import flask
import flask.ext.sqlalchemy
from flask_admin import Admin

# Create the Flask application and the Flask-SQLAlchemy object.
app = flask.Flask(__name__, static_url_path='/static')
app.config.from_object('config')

admin = Admin(app, name='Trombi')

db = SQLAlchemy(app)
