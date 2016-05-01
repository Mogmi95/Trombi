import flask
import flask.ext.sqlalchemy
from flask import render_template, redirect, request
from sqlalchemy.orm import relationship, backref
from sqlalchemy import Table, Column, Integer, ForeignKey, or_
from flask.ext.wtf import Form
from wtforms import StringField, BooleanField, HiddenField
from wtforms.validators import DataRequired

from app import db, app
from models import Person, Team

@app.route("/")
def main():
    return show_all()

@app.route("/all")
def show_all():
    title = "Trombinoscope"
    persons = Person.query.order_by(Person.surname).all()
    return render_template('all.html', persons=persons, title=title)

@app.route("/person/<login>")
def show_person(login=None):
    person = Person.query.filter_by(login=login).first()
    title = person.name + " " + person.surname

    print('Name : ' + person.name)
    print('Manager : ' + str(person.manager))
    print('Subordinates : ' + str(person.subordinates))

    return render_template('person.html', person=person, title=title)

@app.route("/person/vcard/vcard-<login>.vcf")
def show_person_vcard(login=None):
    person = Person.query.filter_by(login=login).first()
    return create_vcard(person)

def create_vcard(person):
    vcard = 'BEGIN:VCARD\n'
    vcard += 'VERSION:3.0\n'
    vcard += 'N:' + person.surname + ';' + person.name + '\n'
    vcard += 'FN:' + person.name + ' ' + person.surname + '\n'
    vcard += 'TITLE:' + person.job + '\n'
    vcard += 'EMAIL;TYPE=PREF,INTERNET:' + person.email + '\n'
    vcard += 'END:VCARD'
    return vcard

@app.route("/search/<query>")
def show_search(query=None):
    title = "Recherche"
    message = "Resultats pour \"" + query + "\" :"
    query = '%' + query + '%'
    persons = Person.query.filter(or_(\
            Person.login.like(query),\
            Person.name.like(query),\
            Person.surname.like(query)))

    if (len(persons.all()) == 1):
        return show_person(persons.first().login)
    return render_template('all.html', persons=persons, message=message, title=title)

@app.route('/search/', methods=['POST'])
def search():
    query = request.form['search']
    return show_search(query)

@app.route("/team")
def show_all_teams():
    title = "Equipes"
    head_team = Team.query.filter_by(high_team=None).first()
    return show_team(head_team.name)


@app.route("/team/<team>")
def show_team(team=None):
    print('HELLO')

    team = Team.query.filter_by(name=team).first()
    title = "Equipe " + team.name

    print("subteam : " + str(team.sub_teams))

    # If the team has sub-teams, we display them. Otherwise we list the persons inside
    if (team.sub_teams is None or team.sub_teams == []):
        print('HEEEEEEEEEEEEERE 1')
        # We show the persons
        root_manager = team.get_manager()
        print('HEEEEEEEEEEEEERE 2')
        print(root_manager)
        treejs = build_treejs_persons(root_manager, True)
        print('HEEEEEEEEEEEEERE 3')
    else:
        # We show the teams inside
        treejs = build_treejs_teams(team)

    print(team.persons)

    return render_template('teamjs.html', team=team, treejs=treejs, title=title)

def build_treejs_teams(root_team):
    print(root_team)
    result = ''

    result += get_node_team(root_team, '')

    for subteam in root_team.sub_teams:
         result += get_node_team(subteam, root_team.name)

    return result

def get_node_team(team, parent):
    return "[{v:'" + team.name + "', f:'<a href=\"/team/"+ team.name +"\"><div class=\"rootTreeNodeElement\">\
        <div class=\"treeNode\">\
            <div class=\"treeNodeText\">"+ team.name +"</div>\
        </div>\
    </div></a>'}, '" + parent + "', '" + team.name + "'],"

def build_treejs_persons(root_person, is_root):
    print(root_person)
    result = ''

    parent = ''
    if (not is_root):
        parent = root_person.manager.login

    #result += "[{v:'" + root_person.login + "', f:'<img class=\"treeImage\" src=\"http://jeanbaptiste.bayle.free.fr/AVATAR/grey_81618-default-avatar-200x200.jpg\" /><p>" + root_person.name + " " + root_person.surname + "</p>'}, '" + root_person.manager.login + "', 'The President'],"
    #result += "[{v:'" + root_person.login + "', f:'<a href=\"/person/" + root_person.login + "\"><div class=\"treeImage\" src=\"/static/images/" + root_person.login + ".jpg\"></div><p>" + root_person.name + " " + root_person.surname + "</p></a>'}, '" + parent + "', 'The President'],"
    result += "[{v:'" + root_person.login + "', f:'<a href=\"/person/"+ root_person.login +"\"><div class=\"rootTreeNodeElement\">\
        <div class=\"treeNode\" style=\"background: url(/static/images/" + root_person.login + ".jpg) center / cover;\" >\
            <div class=\"treeNodeText\">" "</div>\
        </div>\
    </div></a>'}, '" + parent + "', '" + root_person.name + " " + root_person.surname + "'],"


    for subordinate in root_person.subordinates:
        result += build_treejs_persons(subordinate, False)

    return result

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

    persons = []
    managers = {}
    teams = []
    teams_order = {}
    existing_teams = {}

    with open('update_teams.csv', 'r') as f:
        for line in f:
            if (len(line) > 1 and line[0] != '#'):
                split = line[:-1].split(',')
                print(split)
                team = split[0]
                subteam = split[1]

                if (not team in teams):
                    teams.append(team)
                if (not subteam in teams):
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
            print('HEHEHE : ' + str(current_team.sub_teams))
            existing_teams[subteam].high_team = current_team



    # DEPT,SERVICE,LOGIN,NOM,PRENOM,NAISSANCE,FONCTION,MAIL,SKYPE,FIXE,PORTABLE,MANAGER
    with open('update_persons.csv', 'r') as f:
        for line in f:
            if (len(line) > 1 and line[0] != '#'):
                # print(line)
                neo = Person()

                #print('LEUL : ' + str(type(unicode(line))))
                split = line[:-1].split(',')
                neo.login = split[2].strip().lower().decode('utf-8')
                neo.surname = split[3].decode('utf-8')
                neo.name = split[4].decode('utf-8')
                neo.birthday = split[5].decode('utf-8')
                neo.job = split[6].decode('utf-8')
                neo.email = split[7].decode('utf-8')
                neo.skype = split[8].decode('utf-8')
                neo.fixe = split[9].decode('utf-8')
                neo.mobile = split[10].decode('utf-8')


                team = split[1]
                manager = split[11]

                if manager in managers:
                    managers[manager].append(neo)
                else:
                    managers[manager] = [neo]

                if (team in existing_teams):
                    neo.team = existing_teams[team]
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
    print('TEAMS : ' + str(existing_teams))

    db.session.commit()


if __name__ == "__main__":
    db.create_all()

    persons = Person.query.all()
    if (len(persons) == 0):
        load_persons()

    app.run()
