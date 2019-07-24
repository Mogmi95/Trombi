"""The application."""
from flask_sqlalchemy import SQLAlchemy
import flask
from flask_babel import Babel
from flask_migrate import Migrate

# Create the Flask application and the Flask-SQLAlchemy object.
app = flask.Flask(__name__, static_url_path='/static')
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate()
babel = Babel(app)
