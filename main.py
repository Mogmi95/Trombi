#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Hello world test.

Should write something nice here.
"""

import io
import time
import datetime
from flask import render_template, request, url_for
from sqlalchemy import or_
from flask_admin.contrib.sqla import ModelView

from app import db, app, admin
from models import Person, Team

admin.add_view(ModelView(Person, db.session))
admin.add_view(ModelView(Team, db.session))


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
    title = "Trombi"
    persons = Person.query.order_by(Person.surname).all()
    message = "{} persons".format(len(persons))
    return render_template(
        'all.j2',
        persons=persons,
        title=title,
        list_mode=get_list_mode(request),
        list_url='',
        message=message
        )


@app.route("/person/<login>")
def show_person(login=None):
    person = Person.query.filter_by(login=login).first()
    title = person.name + " " + person.surname

    print('Name : ' + person.name)
    print('Manager : ' + str(person.manager))
    print('Subordinates : ' + str(person.subordinates))

    return render_template('person.j2', person=person, title=title)


@app.route("/newpersons")
def show_new_persons():
    title = "New persons"
    last_month_timestamp = time.time() - 2592000
    persons = Person.query.filter(
            Person.arrival > last_month_timestamp
        ).order_by(
            Person.surname
        ).all()
    message = "{} persons".format(len(persons))
    return render_template(
        'all.j2',
        persons=persons,
        title=title,
        list_mode=get_list_mode(request),
        list_url='',
        message=message
        )


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
        'EMAIL;TYPE=PREF,INTERNET:{}\n'\
        'END:VCARD'.format(
            person.surname,
            person.name,
            person.name,
            person.surname,
            person.job,
            person.email
        )
    print(vcard)
    return vcard


@app.route("/search/<query>")
def show_search(query=None):
    title = "Search"
    message = "{} result(s) for \"" + query + "\" :"
    initial_query = query
    query = '%' + query + '%'
    persons = Person.query.filter(or_(
            Person.login.like(query),
            Person.name.like(query),
            Person.job.like(query),
            Person.surname.like(query)))

    if (len(persons.all()) == 1):
        return show_person(persons.first().login)
    return render_template(
        'all.j2',
        persons=persons,
        message=message.format(len(persons.all())),
        title=title,
        list_mode=get_list_mode(request),
        list_url=url_for('show_search', query=initial_query)
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
    for person in persons:
        if (person.birthday != ''):
            birthday_events += u'{{title: "{} {}", start: "2016-{}", url: "/person/{}"}},'.format(
                person.name,
                person.surname,
                person.birthday,
                person.login,
            )
        if (person.arrival != ''):
            arr_date = person.get_arrival_date()
            print(arr_date.month)
            print(arr_date.day)
            arrival_events += u'{{title: "{}", start: "{}", url: "/person/{}"}},'.format(
                u'{} {} ({} years)'.format(person.name, person.surname, 2016 - arr_date.year),
                u'2016-{}-{}'.format(str(arr_date.month).zfill(2), str(arr_date.day).zfill(2)),
                person.login
            )
            # arrival_events += '{title: "' + person.name + ' ' + person.surname + ' (' + person.get_number_of_years() + ' years)", start: "' + person.get_arrival_date() + '", url: "/person/' + person.login + '"},'
    birthday_events += '], color: "#4f60b9", textColor: "#ffffff"'
    arrival_events += '], color: "#e74c3c", textColor: "#ffffff"'

    events_list.append(birthday_events)
    events_list.append(arrival_events)

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

    print(team)
    print("subteam : " + str(team.sub_teams))

    # If the team has sub-teams, we display them.
    # Otherwise we list the persons inside
    if (team.sub_teams is None or team.sub_teams == []):
        # We show the persons
        root_manager = team.get_manager()
        print(root_manager)
        tree = build_tree_persons(root_manager, True)
    else:
        # We show the teams inside
        tree = build_tree_teams(team)

    print(team.persons)

    return render_template(
        'team.j2',
        team=team,
        tree=tree,
        title=title,
        list_mode=get_list_mode(request),
        list_url=''
        )


def build_tree_teams(team):
    print(team)
    result = ''

    # The first item is the manager of all other teams
    team_manager = team.get_manager()
    result += get_node_person(team_manager, '')

    for subteam in team.sub_teams:
        result += get_node_team(subteam, team_manager.login)
        for subsubteam in subteam.sub_teams:
            result += get_node_team(subsubteam, subteam.name)

    return result


def get_node_team(team, parent):
    # TODO : make render_template
    return "[{v:'" + team.name + "', f:'<a href=\"/team/" + team.name + "\"><div class=\"rootTreeNodeElementTeam\">\
        <div class=\"treeNodeTeam\">\
            <div class=\"treeNodeTextTeam\">" + team.name + "</div>\
        </div>\
    </div></a>'}, '" + parent + "', '" + team.name + "'],\n"


def build_tree_persons(root_person, is_root):
    print(root_person)
    result = ''

    parent = ''
    if (not is_root):
        parent = root_person.manager.login

    result += get_node_person(root_person, parent)
    for subordinate in root_person.subordinates:
        result += build_tree_persons(subordinate, False)

    return result


def get_node_person(person, parent):
    # TODO : make render_template
    return "[{v:'" + person.login + "', f:'<a href=\"/person/" + person.login + "\"><div class=\"rootTreeNodeElement\">\
        <div class=\"treeNode\" style=\"background: url(/static/images/photos/" + person.login + ".jpg) center / cover;\" >\
            <div class=\"treeNodeTextContainer\"><div class=\"treeNodeText\">" + person.name + " <br /> " + person.surname + "</div></div>\
        </div>\
    </div></a>'}, '" + parent + "', '" + person.name + " " + person.surname + "'],"


def load_persons():
    # Init teams

    persons = []
    managers = {}
    teams = []
    teams_order = {}
    existing_teams = {}

    # with open('update_teams.csv', 'r') as f:
    with io.open('test_teams.csv', 'r', encoding='utf8') as f:
        for line in f:
            if (len(line) > 1 and line[0] != '#'):
                split = line[:-1].split(',')
                print(split)
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

    print(teams)
    print(teams_order)

    for team_name in teams:
        print(team_name)
        neo_team = Team(team_name)
        existing_teams[team_name] = neo_team
        db.session.add(neo_team)

    for team_name in teams_order:
        current_team = existing_teams[team_name]
        for subteam in teams_order[team_name]:
            existing_teams[subteam].high_team = current_team

    # DEPT;SERVICE;LOGIN;NOM;PRENOM;NAISSANCE;ARRIVEE;FONCTION;MAIL;SKYPE;FIXE;PORTABLE;MANAGER
    with io.open('update_persons.csv', 'r', encoding='utf8') as f:
        for line in f:
            if (len(line) > 1 and line[0] != '#'):
                # print(line)
                neo = Person()

                split = line[:-1].split(';')
                neo.login = split[2].strip().lower()
                neo.surname = split[3]
                neo.name = split[4]
                neo.birthday = format_date(split[5])
                neo.arrival = format_date(split[6])
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
                    print(neo.skype + ' ' + str(neo.team))
                    print('--------------')
                else:
                    print('Error: Missing team ' + team)
                persons.append(neo)

    for person in persons:
        # We link the managers
        if person.login in managers:
            print('Manager : ' + person.login)
            person.subordinates = managers[person.login]
            # for lol in person.subordinates:
            #     print('     -> ' + lol.login)
        db.session.add(person)

    # print('PERSONS : ' + str(persons))
    # print('MANAGERS : ' + str(managers))
    # print('TEAMS : ' + str(existing_teams))

    db.session.commit()


def format_date(date):
    if (date is None or date == ''):
        return 0

    print(date)
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
        return ''

    return result

if __name__ == "__main__":
    db.create_all()

    persons = Person.query.all()
    if (len(persons) == 0):
        load_persons()

    app.run()
