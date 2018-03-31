"""The application."""

from os import path
import io
import time
import datetime
import csv

from werkzeug.security import generate_password_hash

import config
from trombi import admin
from trombi.app import db, app

from trombi.models import TrombiAdmin, Person, Team, Infos
from trombi import views


def load_csv():
    """We create the persons from the data files."""
    persons = []
    managers = {}

    # TEAMS
    existing_teams = {}

    with io.open(config.DATABASE_PERSONS_FILE, 'r', encoding='utf8') as f:
        reader = csv.reader(f, delimiter=',', quotechar='"')
        for row in reader:
            if (len(row) > 1):
                neo = Person()

                neo.login = row[1].strip().lower()
                neo.surname = row[2]
                neo.name = row[3]
                # TODO CHECK NULL
                neo.birthday = datetime.datetime.fromtimestamp(
                    float(format_date(row[4]))
                )
                # TODO CHECK NULL
                neo.arrival = datetime.datetime.fromtimestamp(
                    float(format_date(row[5]))
                )
                neo.job = row[6]
                neo.email = row[7]
                neo.skype = row[8]
                neo.fixe = row[9]
                neo.mobile = row[10]

                # TEAM
                team = row[0]
                if not (team in existing_teams):
                    print('Creating team ' + team + ' for ' + neo.login)
                    neo_team = Team(team)
                    existing_teams[team] = neo_team
                    db.session.add(neo_team)
                neo.team = existing_teams[team]

                # MANAGER
                manager = row[11]
                if manager in managers:
                    managers[manager].append(neo)
                else:
                    managers[manager] = [neo]

                persons.append(neo)

    # We have to commit here first to create Team links
    db.session.commit()

    for person in persons:
        # We link the managers
        if person.login in managers:
            person.subordinates = managers[person.login]
            # We create a team hierarchy
            for subperson in person.subordinates:
                if (subperson.team_id != person.team_id):
                    subperson.team.high_team = person.team
        db.session.add(person)

    db.session.commit()


def format_date(date):
    """Parse the date from the data file."""
    if (date is None or date == ''):
        return 0

    try:
        if (len(date.split('/')) == 3):
            return time.mktime(
                datetime.datetime.strptime(date, u"%Y/%m/%d").timetuple()
                )
        else:
            return time.mktime(
                datetime.datetime.strptime(date, "%d/%m").timetuple()
                )
    except:
        print('Cannot convert : ' + date)
        return 0

    return ''


def are_config_files_present():
    """Check if all needed files are present."""
    if (not path.isfile('config.py')):
        print('Error: No config file. Use "cp config-example.py config.py".')
        return False
    if (not path.isfile(config.DATABASE_PERSONS_FILE)):
        print('Error: Missing : ' + config.DATABASE_PERSONS_FILE)
        return False
    return True


if __name__ == "__main__":
    """Entry point."""
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


    # We check that the config file exists
    if (are_config_files_present()):
        persons = Person.query.all()

        if (len(persons) == 0):
            load_csv()

            # We create an administrator
            superadmin = TrombiAdmin()
            superadmin.login = config.ADMIN_LOGIN
            superadmin.password = generate_password_hash(config.ADMIN_PASSWORD)
            db.session.add(superadmin)
            db.session.commit()
        app.run(port=config.PORT)
    else:
        print("Terminated.")
