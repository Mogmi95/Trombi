import flask
import flask.ext.sqlalchemy
from flask import render_template, redirect, request
from sqlalchemy.orm import relationship, backref
from sqlalchemy import Table, Column, Integer, ForeignKey
from flask.ext.wtf import Form
from wtforms import StringField, BooleanField, HiddenField
from wtforms.validators import DataRequired

from app import db, app
from models import Person, Team

@app.route("/")
def main():
    teams = Team.query.all()
    return render_template('index.html', teams=teams)

@app.route("/all")
def show_all():
    persons = Person.query.all()
    return render_template('all.html', persons=persons)

@app.route("/person/<login>")
def show_person(login=None):
    person = Person.query.filter_by(login=login).first()
    return render_template('person.html', person=person)

@app.route("/search/<query>")
def show_search(query=None):
    persons = Person.query.filter_by(login=query)

    if (len(persons.all()) == 1):
        return render_template('person.html', person=persons.first())


    return render_template('all.html', persons=persons)

@app.route('/search/', methods=['POST'])
def search():
    query = request.form['search']
    return show_search(query)

@app.route("/team/<team>")
def show_team(team=None):
    team = Team.query.filter_by(name=team).first()
    root_manager = team.get_manager()

    print('Manager : ' + str(root_manager))

    tree = build_tree(root_manager, True)

    return render_template('team.html', team=team, tree=tree)

# Return a HTML tree with a person as root
def build_tree(root_person, is_root):
    result = ''

    if (is_root):
        result = '<ul><li>\n'
    result += render_template('tree_node.html', person=root_person, smallpics=True)

    if (len(root_person.subordinates) > 0):
        result += '\n<ul>\n'
        for subordinate in root_person.subordinates:
            result += '<li>\n'
            result += build_tree(subordinate, False)
            result += '</li>\n'
        result += '\n</ul>\n'

    if (is_root):
        result += '\n</li></ul>\n'
    return result

def load_persons():
    # Init teams
    apps = Team('apps');
    db.session.add(apps)
    db.session.commit()

    persons = []
    managers = {}
    with open('update.txt', 'r') as f:
        for line in f:
            if (len(line) > 0 and line[0] != '#'):
                print(line)
                neo = Person()
                split = line.split(';')

                neo.team = Team.query.filter_by(name=split[0]).first()
                neo.login = split[1]
                neo.surname = split[2]
                neo.name = split[3]
                neo.birthday = split[4]
                neo.job = split[5]
                neo.email = split[6]
                neo.skype = split[7]
                neo.fixe = split[8]
                neo.mobile = split[9]

                manager = split[10]

                if manager in managers:
                    managers[manager].append(neo)
                else:
                    managers[manager] = [neo]

                persons.append(neo)

    print('PERSONS : ' + str(persons))
    print('MANAGERS : ' + str(managers))

    for person in persons:
        # We link the managers
        if person.login in managers:
            person.subordinates = managers[person.login]
        db.session.add(person)

    db.session.commit()


if __name__ == "__main__":
    db.create_all()

    persons = Person.query.all()
    if (len(persons) == 0):
        load_persons()

    app.run()
