#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Hello world test.

Should write something nice here.
"""

import time
import datetime
import random
import os
import json
from flask import render_template, request, url_for, redirect, send_file, send_from_directory
from sqlalchemy import or_
from flask.ext.babel import gettext

from config import LANGUAGES, PHOTOS_FOLDER, WEBSITE_URL
from app import db, app, babel
from models import Person, PersonComment, Team, Infos, Link, Room, Floor


@babel.localeselector
def get_locale():
    """Get the locale to use for lang."""
    locale = request.accept_languages.best_match(LANGUAGES.keys())
    # return locale
    # Temporary
    return 'en'


@app.errorhandler(404)
def page_not_found(e):
    """Custom 404 page."""
    return render_template('404.html')


def get_list_mode(request):
    """Get the current display mode for the dashboard."""
    list_mode = request.args.get('list')
    if (list_mode != 'true'):
        list_mode = None
    return list_mode


@app.route("/")
def main():
    """Root view."""
    return show_all()


@app.route("/photo/<login>")
def person_image(login=None):
    """Get picture for person, or default picture."""
    filepath = os.path.join(PHOTOS_FOLDER, login + ".jpg")
    if (os.path.isfile(filepath)):
        return send_from_directory(PHOTOS_FOLDER, login + ".jpg")
    else:
        return redirect(url_for('static', filename='images/missing_avatar.png'))

@app.route("/all")
def show_all():
    """Show a list of all persons in the trombi."""
    person_filter = request.args.get('filter')
    title = gettext(u'Trombi')

    persons_to_display = []

    # We get the text to display in the top header
    header_text = Infos.query.first().text

    if (person_filter in ["newcomers"]):
        # Calculating newcomers
        last_month_timestamp = time.time() - 2592000
        last_month_date = datetime.datetime.fromtimestamp(last_month_timestamp)
        persons_to_display = Person.query.filter(
                Person.arrival > last_month_date
            ).order_by(
                Person.surname
            ).all()
    else:
        persons_to_display = Person.query.order_by(Person.surname).all()

    return render_template(
        'all.html',
        persons=persons_to_display,
        title=title,
        list_mode=get_list_mode(request),
        person_filter=person_filter,
        list_url='',
        header_text=header_text
        )


@app.route("/person/<login>")
def show_person(login=None):
    """Display information about a specific person."""
    commented = request.args.get('commented')
    person = Person.query.filter_by(login=login).first()
    if (person is None):
        title = gettext(u'%(login)s doesn\'t exists.', login=login)
        return render_template('person_error.html', person=person, title=title)
    else:
        title = person.name + ' ' + person.surname
        return render_template(
            'person.html',
            person=person,
            title=title,
            commented=commented,
        )

@app.route('/api/maps')
def get_maps_info():
    """
    Return a list of all the floors with their rooms
    """
    floors = Floor.query.all()

    floordata = []
    for floor in floors:
        data = floor.as_dict()
        data['rooms'] = [room.as_dict() for room in floor.rooms]
        floordata.append(data)

    return '{"floors": ' + str(floordata).replace("u'", "'").replace("'", "\"") + '}'

@app.route('/person/<login>/edit')
def show_person_report(login=None):
    """Report an error on a person's profile."""
    #person_login = request.form.get('personId')
    person = Person.query.filter_by(login=login).first()
    floors = Floor.query.all()
    print(person)
    return render_template(
        "person_report.html",
        person=person,
        floors=floors,
    )

@app.route('/person/<login>/edit/confirm', methods=['POST'])
def person_edit(login=None):
    """Submit an edit for a person."""
    inputId = request.form.get('id')
    inputComment = request.form.get('comment')
    inputRoom = request.form.get('roomId')
    person = Person.query.filter_by(id=inputId).first()
    room = Room.query.filter_by(id=inputRoom).first()
    # person.room = room
    person_comment = PersonComment()
    person_comment.message = inputComment.replace('<', '(').replace('>', ')')
    person_comment.pending_room_id = room.id
    person.comments.append(person_comment)
    db.session.add(person_comment)
    db.session.commit()
    return "Added comment OK " + inputRoom


@app.route('/person/comment', methods=['POST'])
def person_comment():
    """Add a comment on a person."""
    comment = request.form.get('comment')
    login = request.form.get('login')
    person = Person.query.filter_by(login=login).first()
    person_comment = PersonComment()
    person_comment.message = comment.replace('<', '(').replace('>', ')')
    person.comments.append(person_comment)
    db.session.commit()
    return redirect(url_for('show_person', login=login, commented=True))


@app.route("/map")
def show_map():
    """Base screen to access information about floors and rooms."""
    return get_map_information()

@app.route("/map/room/<room_id>")
def show_map_room(room_id=None):
    """Display a room on a map."""
    return get_map_information(room_id=room_id)


@app.route("/map/floor/<floor_id>")
def show_map_floor(floor_id=None):
    """Display a floor on a map."""
    return get_map_information(floor_id=floor_id)

def get_map_information(room_id=None, floor_id=None):
    """Get information to display a map"""
    rooms = Room.query.all()
    if rooms is None:
        rooms = []
    floors = Floor.query.all()
    if floors is None:
        floors = []

    title="Map"

    selected_floor = None
    selected_room = None

    if room_id is not None:
        # Displaying a room
        selected_room = Room.query.filter_by(id=room_id).first()
        selected_floor = selected_room.floor
    elif floor_id is not None:
        # Displaying a floor
        selected_floor = Floor.query.filter_by(id=floor_id).first()
        pass
    else:
        # Displaying nothing
        pass

    return render_template(
        'maps.html',
        rooms=rooms,
        floors=floors,
        selected_room=selected_room,
        selected_floor=selected_floor,
        title=title,
    )


@app.route("/infos")
def show_infos():
    """Display various information stored in the database."""
    # TODO: Should not be hardcoded
    infos = db.session.query(Infos).all()[1]
    if (infos is None):
        text = gettext(u'Nothing here yet.')
    else:
        text = infos.text
    return render_template('infos.html', text=text)


@app.route("/person/vcard/vcard-<login>.vcf")
def show_person_vcard(login=None):
    """Show a Person's VCard."""
    person = Person.query.filter_by(login=login).first()
    return person.create_vcard()

def perform_search(query):
    """Return a set containing all the matches for the query"""
    result = {}

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

    result['persons'] = []
    for person_key in hash_persons.keys():
        result['persons'].append(hash_persons[person_key])

    return result

@app.route("/search/<query>")
def show_search(query=None):
    """The search screen."""
    title = gettext(u'Search')
    message = gettext(
        u'%(number)s result(s) for \"%(query)s\" :', number='{}',
        query=query
    )

    search_result = perform_search(query)
    persons = []
    if 'persons' in search_result:
        persons = search_result["persons"]

    #if (len(persons) == 1):
    #    return redirect(url_for('show_person', login=persons[0]))
    return render_template(
        'search.html',
        search_result=search_result,
        is_in_search_mode=True,
        persons=persons,
        message=message.format(len(persons)),
        title=title,
        list_mode=get_list_mode(request),
        list_url=url_for('show_search', query=query),
        header_text=None
        )

@app.route("/api/search")
def api_search():

    # Searching for persons
    persons = []
    if ('q' in request.args):
        query = request.args['q']
        print(query)
        search_result = perform_search(query)
        persons = []
        if 'persons' in search_result:
            persons = search_result["persons"]

    person_results = []
    curr = 0
    for person in persons:
        tmp = {}
        curr += 1
        tmp['id'] = curr
        tmp['text'] = person.surname.capitalize() + " " + person.name.capitalize() + " - " + person.job.capitalize()
        person_results.append(tmp)

    # Putting all the results inside a single JSON
    result = '\
    {\
        "results": ['\
        + '{"text": "People", "children":' + json.dumps(person_results) + '}'\
        '\
    ]}\
    '.replace("u\'", "\'").strip()
    print(result)
    return result

@app.route('/search/', methods=['POST'])
def search():
    """Handle the search results."""
    query = request.form['search']
    return show_search(query)


@app.route("/calendar")
def show_calendar():
    """The calendar screen."""
    title = gettext(u'Calendar')
    persons = Person.query.all()

    events_list = []

    # Persons events
    birthday_events = '['
    arrival_events = '['
    for year in [2018, 2019]:
        for person in persons:
            if (person.birthday != ''):
                birth_date = person.birthday
                birthday_events += (u'{{title: "{} {}", start: "{}",' +
                                    ' url: "/person/{}"}},').format(
                    person.name,
                    person.surname,
                    u'{}-{}-{}'.format(
                        year,
                        str(birth_date.month).zfill(2),
                        str(birth_date.day).zfill(2)
                    ),
                    person.login
                )
            if (person.arrival != ''):
                arr_date = person.arrival
                # TODO : don't harcode the current year
                if (year - arr_date.year <= 0):
                    arrival_text = gettext(u'arrival')
                else:
                    fdate = year - arr_date.year
                    arrival_text = gettext(u'%(number)s years', number=fdate)

                arrival_events += (u'{{title: "{}", start: "{}",' +
                                   u' url: "/person/{}"}},').format(
                        u'{} {} ({})'.format(
                            person.name,
                            person.surname,
                            arrival_text
                        ),
                        u'{}-{}-{}'.format(
                            year,
                            str(arr_date.month).zfill(2),
                            str(arr_date.day).zfill(2)
                        ),
                        person.login
                    )
    birthday_events += '], color: "#a9d03f", textColor: "#ffffff"'
    arrival_events += '], color: "#368cbf", textColor: "#ffffff"'

    events_list.append(birthday_events)
    events_list.append(arrival_events)

    # events = '[{title: "Pizza", start: "2016-05-06"}]'

    return render_template(
        'calendar.html',
        title=title,
        events_list=events_list)


@app.route("/team")
def show_all_teams():
    """Show a graph with all teams."""
    head = Person.query.filter_by(manager=None).first()
    return show_team(head.team.name)


@app.route("/team/<team>")
def show_team(team=None):
    """Show a graph for a specific team."""
    team = Team.query.filter_by(name=team).first()
    title = gettext(u'Team %(team_name)s', team_name=team.name)

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
        'team.html',
        team=team,
        tree=tree,
        title=title,
        list_mode=get_list_mode(request),
        list_url=''
        )


def build_tree_teams(team):
    """Default method to build a tree for a given team."""
    result = get_node_team(team, '')

    for subteam in team.sub_teams:
        result += get_node_team(subteam, team.name)
        # Uncomment for more levels, only 2 now
        # for subsubteam in subteam.sub_teams:
        #    result += get_node_team(subsubteam, subteam.name)

    return result


def get_node_team(team, parent):
    """Default method to build a node for a given team."""
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
    """Default method to build a tree for a given person."""
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
    """Default method to build a node for a given person."""
    # TODO : make render_template
    return "[{v:'" + person.login + "', f:'<div class=\"rootTreeNodeElement\"><a href=\"/person/" + person.login + "\">\
        <div class=\"rootTreeNodeElementFiller\" style=\"background: url(/photo/"+ person.login + ") center / cover;\" >\
            <div class=\"treeNodeTextContainer\"><div class=\"treeNodeText\">" + person.name.replace('\'','\\\'') + "</div></div>\
        </div>\
    </a></div>'}, '" + parent + "', '" + person.name.replace('\'','\\\'') + " " + person.surname.replace('\'','\\\'') + "'],"

# Game

@app.route('/game', methods=['GET', 'POST'])
def show_game():
    """"Display a game to learn who's who in the company."""
    # We create another person to find

    all = Person.query.all()
    random.shuffle(all)
    person = all[0]
    persons = []

    for i in range(min(8, len(all))):
        persons.append(all[i])

    random.shuffle(persons)

    return render_template(
        'game.html',
        title='Game',
        person=person,
        persons=persons,
    )

# Links

@app.route("/links")
def show_links(login=None):
    """Display all links."""
    links = Link.query.order_by(Link.order).all()
    if (len(links) == 0) :
        links = None
    return render_template(
            'links.html',
            links=links,
        )

# API

@app.route("/api/persons", defaults={'login': None}, methods=["GET"])
@app.route("/api/persons/<login>", methods=["GET"])
def api_persons(login=None):
    """API to get all the persons"""
    persons = None
    json_persons = []

    if (login != None):
        persons = Person.query.filter_by(login=login).all()
        if (len(persons) == 0):
            # Error, the person doesn't exist
            return '{ error: "User doesn\'t exist" }', 404
    else:
        persons = Person.query.order_by(Person.login).all()

    for person in persons:
        json_person = {}
        json_person["id"] = person.id
        json_person["login"] = person.login
        json_person["name"] = person.name
        json_person["surname"] = person.surname
        json_person["birthday"] = person.get_birthday_date_timestamp()
        json_person["arrival"] = person.get_arrival_date_timestamp()
        json_person["email"] = person.email
        json_person["job"] = person.job
        json_person["team_id"] = person.team_id
        json_person["picture"] = url_for('person_image', login=person.login)
        json_persons.append(json_person)

    return json.dumps(json_persons)

@app.route("/api/teams", defaults={'team_id': None}, methods=["GET"])
@app.route("/api/teams/<team_id>", methods=["GET"])
def api_teams(team_id=None):
    """API to get all the teams"""
    teams = None
    json_teams = []

    if (team_id != None):
        teams = Team.query.filter_by(team_id=team_id).all()
        if (len(teams) == 0):
            # Error, the person doesn't exist
            return '{ error: "Team doesn\'t exist" }', 404
    else:
        teams = Team.query.order_by(Team.id).all()

    for team in teams:
        json_team = {}
        json_team["id"] = team.id
        json_team["name"] = team.name
        if (team.high_team != None):
            json_team["higher_teaml_id"] = team.high_team.id
        json_team["persons"] = [person.login for person in team.persons]
        json_teams.append(json_team)

    return json.dumps(json_teams)

@app.route("/api/links", methods=["GET"])
def api_links():
    """API to get all the links"""
    links = Link.query.order_by(Link.id).all()
    json_links = []

    for link in links:
        json_link = {}
        json_link["id"] = link.id
        json_link["url"] = link.url
        json_link["image_url"] = link.image
        json_link["title"] = link.title
        json_link["description"] = link.description
        json_links.append(json_link)

    return json.dumps(json_links)
