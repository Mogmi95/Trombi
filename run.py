"""The application."""

from os import path
import io
import time
import datetime

from werkzeug.security import generate_password_hash

import config
from trombi import admin
from trombi.app import db, app

from trombi.models import TrombiAdmin, Person, Team
from trombi import views


def load_teams():
    """We create the teams from the data files."""
    teams = []
    teams_order = {}
    existing_teams = {}

    with io.open(config.DATABASE_TEAMS_FILE, 'r', encoding='utf8') as f:
        for line in f:
            if (len(line) > 1 and line[0] != '#'):
                split = line[:-1].split(';')
                team = split[0]
                subteam = split[1]

                if (team not in teams):
                    teams.append(team)
                if (subteam not in teams):
                    teams.append(subteam)

                if team in teams_order:
                    teams_order[team].append(subteam)
                else:
                    teams_order[team] = [subteam]

    for team_name in teams:
        neo_team = Team(team_name)
        existing_teams[team_name] = neo_team
        db.session.add(neo_team)

    for team_name in teams_order:
        current_team = existing_teams[team_name]
        for subteam in teams_order[team_name]:
            existing_teams[subteam].high_team = current_team

    db.session.commit()


def load_persons():
    """We create the persons from the data files."""
    persons = []
    managers = {}

    # TEAMS
    existing_teams = {}
    teams = Team.query.all()
    for team in teams:
        existing_teams[team.name] = team

    with io.open(config.DATABASE_PERSONS_FILE, 'r', encoding='utf8') as f:
        for line in f:
            if (len(line) > 1 and line[0] != '#'):
                neo = Person()

                split = line[:-1].split(';')
                neo.login = split[2].strip().lower()
                neo.surname = split[3]
                neo.name = split[4]
                neo.birthday = datetime.datetime.fromtimestamp(
                    float(format_date(split[5]))
                )
                neo.arrival = datetime.datetime.fromtimestamp(
                    float(format_date(split[6]))
                )
                neo.job = split[7]
                neo.email = split[8]
                neo.skype = split[9]
                neo.fixe = split[10]
                neo.mobile = split[11]

                team = split[1]
                manager = split[12]
                if manager in managers:
                    managers[manager].append(neo)
                else:
                    managers[manager] = [neo]

                if (team in existing_teams):
                    neo.team = existing_teams[team]
                else:
                    print('Error: Missing team ' + team + ' for ' + neo.login)
                persons.append(neo)

    for person in persons:
        # We link the managers
        if person.login in managers:
            person.subordinates = managers[person.login]
        db.session.add(person)
    db.session.commit()


def format_date(date):
    """Parse the date from the data file."""
    if (date is None or date == ''):
        return 0

    try:
        if (len(date.split('/')) == 3):
            return time.mktime(
                datetime.datetime.strptime(date, "%m/%d/%Y").timetuple()
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
    if (not path.isfile(config.DATABASE_TEAMS_FILE)):
        print('Error: Missing : ' + config.DATABASE_TEAMS_FILE)
        return False
    return True


if __name__ == "__main__":
    """Entry point."""
    db.create_all()
    admin.init()

    # We check that the config file exists
    if (are_config_files_present()):
        persons = Person.query.all()
        if (len(persons) == 0):
            load_teams()
            load_persons()

            # We create an administrator
            superadmin = TrombiAdmin()
            superadmin.login = config.ADMIN_LOGIN
            superadmin.password = generate_password_hash(config.ADMIN_PASSWORD)
            db.session.add(superadmin)
            db.session.commit()
        app.run(port=5000)
    else:
        print("Terminated.")
