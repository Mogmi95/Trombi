#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Hello world test.

Should write something nice here.
"""

import io
import time
import datetime
from os import path
from flask import render_template, request, url_for, redirect
from wtforms import form, fields, validators
from sqlalchemy import or_
from flask_admin.contrib import sqla
from flask_admin import helpers, expose
import config
import flask_admin as flask_admin

import flask_login as login
from werkzeug.security import generate_password_hash, check_password_hash


from app import db, app
from models import Person, Team, TrombiAdmin, Trivia, Room


# LOGIN PART

# Define login and registration forms (for flask-login)
class LoginForm(form.Form):
    login = fields.StringField(u'Login', validators=[validators.required()])
    password = fields.PasswordField(u'Password', validators=[validators.required()])

    def validate_login(self, field):
        user = self.get_user()

        if user is None:
            raise validators.ValidationError('Invalid user')

        if not check_password_hash(user.password, self.password.data):
            raise validators.ValidationError('Invalid password')

    def get_user(self):
        return db.session.query(TrombiAdmin).filter_by(login=self.login.data).first()


# Initialize flask-login
def init_login():
    login_manager = login.LoginManager()
    login_manager.init_app(app)

    # Create user loader function
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.query(TrombiAdmin).get(user_id)



# Create customized index view class that handles login & registration
class MyAdminIndexView(flask_admin.AdminIndexView):

    @expose('/')
    def index(self):
        if not login.current_user.is_authenticated:
            return redirect(url_for('.login_view'))
        return super(MyAdminIndexView, self).index()

    @expose('/login/', methods=('GET', 'POST'))
    def login_view(self):
        # handle user login
        form = LoginForm(request.form)
        if helpers.validate_form_on_submit(form):
            user = form.get_user()
            login.login_user(user)

        if login.current_user.is_authenticated:
            return redirect(url_for('.index'))
        #link = '<p>Don\'t have an account? <a href="' + url_for('.register_view') + '">Click here to register.</a></p>'
        self._template_args['form'] = form
        return super(MyAdminIndexView, self).index()

    @expose('/logout/')
    def logout_view(self):
        login.logout_user()
        return redirect(url_for('.index'))

from wtforms.widgets import TextArea
from wtforms.fields import TextAreaField

class CKEditorWidget(TextArea):
    def __call__(self, field, **kwargs):
        if kwargs.get('class'):
            kwargs['class'] += " ckeditor"
        else:
            kwargs.setdefault('class', 'ckeditor')
        return super(CKEditorWidget, self).__call__(field, **kwargs)

class CKEditorField(TextAreaField):
    widget = CKEditorWidget()

# Create customized model view class
class MyModelView(sqla.ModelView):
    def is_accessible(self):
        return login.current_user.is_authenticated
    # Change edit in the admin
    form_overrides = dict(text=CKEditorField)
    can_view_details = True
    create_template = 'edit.html'
    edit_template = 'edit.html'


# Initialize flask-login
init_login()

# Create admin
admin = flask_admin.Admin(app, 'Trombi admin', index_view=MyAdminIndexView(), base_template='master.html')

# Add view

# Do we want the admin to editate this ?
# admin.add_view(MyModelView(TrombiAdmin, db.session))

admin.add_view(MyModelView(Person, db.session))
admin.add_view(MyModelView(Team, db.session))
admin.add_view(MyModelView(Room, db.session))
admin.add_view(MyModelView(Trivia, db.session))

# END LOGIN TEST

def get_list_mode(request):
    list_mode = request.args.get('list')
    if (list_mode != 'true'):
        list_mode = None
    return list_mode


@app.route("/")
def main():
    return show_all()


@app.route("/all")
def show_all():
    person_filter = request.args.get('filter')
    title = "Trombi"

    if (person_filter is not None):
        last_month_timestamp = time.time() - 2592000
        persons = Person.query.filter(
                Person.arrival > last_month_timestamp
            ).order_by(
                Person.surname
            ).all()
        message = "{} newbies".format(len(persons))
    else:
        persons = Person.query.order_by(Person.surname).all()
        message = "{} people".format(len(persons))
    return render_template(
        'all.j2',
        persons=persons,
        title=title,
        list_mode=get_list_mode(request),
        person_filter=person_filter,
        list_url='',
        message=message
        )


@app.route("/person/<login>")
def show_person(login=None):
    person = Person.query.filter_by(login=login).first()
    title = person.name + " " + person.surname

    return render_template('person.j2', person=person, title=title)


@app.route("/trivia")
def show_trivia():
    trivia = db.session.query(Trivia).first()
    if (trivia is None):
        text = u'Nothing here yet.'
    else:
        text = trivia.text
    return render_template('trivia.j2', text=text)

@app.route("/person/vcard/vcard-<login>.vcf")
def show_person_vcard(login=None):
    person = Person.query.filter_by(login=login).first()
    return create_vcard(person)


def create_vcard(person):
    vcard = \
        'BEGIN:VCARD\n'\
        'VERSION:3.0\n'\
        'N:{};{}\n'\
        'FN:{} {}\n'\
        'TITLE:{}\n'\
        'TEL;TYPE=WORK,VOICE:{}\n'\
        'EMAIL;TYPE=PREF,INTERNET:{}\n'\
        'END:VCARD'.format(
            person.surname,
            person.name,
            person.name,
            person.surname,
            person.job,
            person.mobile,
            person.email
        )
    return vcard


@app.route("/search/<query>")
def show_search(query=None):
    title = "Search"
    message = "{} result(s) for \"" + query + "\" :"

    # Maybe re-do this part of the code in a more pytonic way
    hash_persons = {}
    for token in query.split(' '):
        persons = Person.query.filter(or_(
            Person.login.like('%' + token + '%'),
            Person.name.like('%' + token + '%'),
            Person.job.like('%' + token + '%'),
            Person.surname.like('%' + token + '%')))

        for person in persons.all():
            hash_persons[person.login] = person

    persons = []
    for person_key in hash_persons.keys():
        persons.append(hash_persons[person_key])

    if (len(persons) == 1):
        return show_person(persons[0].login)
    return render_template(
        'all.j2',
        persons=persons,
        message=message.format(len(persons)),
        title=title,
        list_mode=get_list_mode(request),
        list_url=url_for('show_search', query=query)
        )


@app.route('/search/', methods=['POST'])
def search():
    query = request.form['search']
    return show_search(query)


@app.route("/calendar")
def show_calendar():
    title = "Calendar"
    persons = Person.query.all()

    events_list = []

    # Persons events
    birthday_events = '['
    arrival_events = '['
    for year in [2016, 2017]:
        for person in persons:
            if (person.birthday != ''):
                birth_date = person.birthday
                birthday_events += u'{{title: "{} {}", start: "{}", url: "/person/{}"}},'.format(
                    person.name,
                    person.surname,
                    u'{}-{}-{}'.format(year, str(birth_date.month).zfill(2), str(birth_date.day).zfill(2)),
                    person.login,
                )
            if (person.arrival != ''):
                arr_date = person.arrival
                # TODO : don't harcode the current year
                if (year - arr_date.year <= 0):
                    arrival_text = 'arrival'
                else:
                    arrival_text = u'{} years'.format(2016 - arr_date.year)
                arrival_events += u'{{title: "{}", start: "{}", url: "/person/{}"}},'.format(
                    u'{} {} ({})'.format(person.name, person.surname, arrival_text),
                    u'{}-{}-{}'.format(year, str(arr_date.month).zfill(2), str(arr_date.day).zfill(2)),
                    person.login
                )
                # arrival_events += '{title: "' + person.name + ' ' + person.surname + ' (' + person.get_number_of_years() + ' years)", start: "' + person.arrival + '", url: "/person/' + person.login + '"},'
    birthday_events += '], color: "#a9d03f", textColor: "#ffffff"'
    arrival_events += '], color: "#368cbf", textColor: "#ffffff"'

    netatmevents = '[{title: "BBQ Boss", start: "2016-07-05", url: ""}], color: "#db6b1a", textColor: "#ffffff"'

    events_list.append(birthday_events)
    events_list.append(arrival_events)
    events_list.append(netatmevents)

    # events = '[{title: "Pizza", start: "2016-05-06"}]'

    return render_template(
        'calendar.j2',
        title=title,
        events_list=events_list)


@app.route("/team")
def show_all_teams():
    head_team = Team.query.filter_by(high_team=None).first()
    return show_team(head_team.name)


@app.route("/team/<team>")
def show_team(team=None):
    team = Team.query.filter_by(name=team).first()
    title = "Team " + team.name

    # If the team has sub-teams, we display them.
    # Otherwise we list the persons inside
    if (team.sub_teams is None or team.sub_teams == []):
        # We show the persons
        team_root_persons = team.get_root_persons()
        tree = build_tree_persons(team_root_persons, True)
    else:
        # We show the teams inside
        tree = build_tree_teams(team)

    return render_template(
        'team.j2',
        team=team,
        tree=tree,
        title=title,
        list_mode=get_list_mode(request),
        list_url=''
        )


def build_tree_teams(team):
    result = ''

    # The first item is the manager of all other teams

    # if (team_manager.login == 'fpotter'):
    result += get_node_team(team, '')
    # else
    # result += get_node_person(team_manager, '')

    for subteam in team.sub_teams:
        result += get_node_team(subteam, team.name)
        for subsubteam in subteam.sub_teams:
            result += get_node_team(subsubteam, subteam.name)

    return result


def get_node_team(team, parent):
    # TODO : make render_template
    # TODO : add a better way to handle invisible blocks
    if (team.name == '1'):
        # We display only a vertical bar
        return "[{v:'" + team.name + "', f:'<div class=\"rootTreeNodeElement\" >\
                    <div class=\"verticalLine\"></div>\
                    </div>'}, '" + parent + "', '" + team.name + "'],\n"
    else:
        return "[{v:'" + team.name + "', f:'<div class=\"rootTreeNodeElement\" >\
                    <a href=\"/team/" + team.name + "\"><div class=\"rootTreeNodeElementFiller\" >\
                    <div class=\"rootTreeNodeLinkCenter\"><div class=\"rootTreeNodeLinkCenterChild\">" + team.name + "</div></div></div></a>\
                    </div>'}, '" + parent + "', '" + team.name + "'],\n"


def build_tree_persons(team_root_persons, is_root):
    result = ''
    parent = ''

    if (is_root):
        parent_team_manager = team_root_persons[0].manager
        result += get_node_person(parent_team_manager, '')
        parent = parent_team_manager.login
    else:
        parent = team_root_persons[0].manager.login

    for root_person in team_root_persons:
        result += get_node_person(root_person, parent)
        for subordinate in root_person.subordinates:
            result += build_tree_persons([subordinate], False)

    return result


def get_node_person(person, parent):
    # TODO : make render_template
    return "[{v:'" + person.login + "', f:'<div class=\"rootTreeNodeElement\"><a href=\"/person/" + person.login + "\">\
        <div class=\"rootTreeNodeElementFiller\" style=\"background: url(/static/images/photos/" + person.login + ".jpg) center / cover;\" >\
            <div class=\"treeNodeTextContainer\"><div class=\"treeNodeText\">" + person.name + " <br /> " + person.surname.upper() + "</div></div>\
        </div>\
    </a></div>'}, '" + parent + "', '" + person.name + " " + person.surname + "'],"

# DATABASE INIT

def load_teams():
    # Init teams
    teams = []
    teams_order = {}
    existing_teams = {}

    # We try to use a custom teams file if it exists. If not, default file
    if (path.isfile(config.DATABASE_TEAMS_FILE)):
        teams_file = config.DATABASE_TEAMS_FILE
    else:
        teams_file = config.DATABASE_TEAMS_DEFAULT_FILE

    with io.open(teams_file, 'r', encoding='utf8') as f:
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

def load_rooms():
    # Init rooms
    # We try to use a custom teams file if it exists. If not, default file
    if (path.isfile(config.DATABASE_ROOMS_FILE)):
        rooms_file = config.DATABASE_ROOMS_FILE
    else:
        rooms_file = config.DATABASE_ROOMS_DEFAULT_FILE

    with io.open(rooms_file, 'r', encoding='utf8') as f:
        for line in f:
            if (len(line) > 1 and line[0] != '#'):
                split = line[:-1].split(';')
                room_name = split[0]
                floor_number = split[1]
                neo_room = Room(room_name, floor_number)
                db.session.add(neo_room)

    db.session.commit()


def load_persons():
    persons = []
    managers = {}

    # TEAMS
    existing_teams = {}
    teams = Team.query.all()
    for team in teams:
        existing_teams[team.name] = team

    # ROOMS
    existing_rooms = {}
    rooms = Room.query.all()
    for room in rooms:
        existing_rooms[room.name] = room

    # We try to use a custom persons file if it exists. If not, default file
    if (path.isfile(config.DATABASE_PERSONS_FILE)):
        persons_file = config.DATABASE_PERSONS_FILE
    else:
        persons_file = config.DATABASE_PERSONS_DEFAULT_FILE

    with io.open(persons_file, 'r', encoding='utf8') as f:
        for line in f:
            if (len(line) > 1 and line[0] != '#'):
                neo = Person()

                split = line[:-1].split(';')
                neo.login = split[2].strip().lower()
                neo.surname = split[3]
                neo.name = split[4]
                neo.birthday = datetime.datetime.fromtimestamp(float(format_date(split[5])))
                neo.arrival = datetime.datetime.fromtimestamp(float(format_date(split[6])))
                neo.job = split[7]
                neo.email = split[8]
                neo.skype = split[9]
                neo.fixe = split[10]
                neo.mobile = split[11]

                team = split[1]
                manager = split[12]
                # room = split[13]

                if manager in managers:
                    managers[manager].append(neo)
                else:
                    managers[manager] = [neo]

                if (team in existing_teams):
                    neo.team = existing_teams[team]

                # if (room in existing_rooms):
                #    neo.room = existing_rooms[room]

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

if __name__ == "__main__":
    db.create_all()

    persons = Person.query.all()
    if (len(persons) == 0):
        load_teams()
        # load_rooms()
        load_persons()

        superadmin = TrombiAdmin()
        superadmin.login = "admin"
        superadmin.password = generate_password_hash("pizza")
        db.session.add(superadmin)
        db.session.commit()

    app.run(port=5000)
