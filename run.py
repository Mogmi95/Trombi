"""The application."""

from os import path
import io
import time
import datetime
import csv
import config

from werkzeug.security import generate_password_hash

from trombi import admin
from trombi.app import db, app
from trombi.models import TrombiAdmin, Person, Team, Infos
from trombi import views


def are_config_files_present():
    """Check if all needed files are present."""
    if (not path.isfile('config.py')):
        print('Error: No config file. Use "cp config-example.py config.py".')
        return False
    return True


if __name__ == "__main__":
    if (are_config_files_present()):
        db.create_all()
        admin.init()

        # We create basics Info if needed
        infos = Infos.query.all()
        if (len(infos) == 0):
            header_text = Infos()
            news_text = Infos()
            db.session.add(header_text)
            db.session.add(news_text)
            db.session.commit()
        
        admins = TrombiAdmin.query.all()
        if (len(admins) == 0):
            # We create an administrator
            superadmin = TrombiAdmin()
            superadmin.login = config.ADMIN_LOGIN
            superadmin.password = generate_password_hash(config.ADMIN_PASSWORD)
            db.session.add(superadmin)
            db.session.commit()
        app.run(port=config.PORT, threaded=True)
