import datetime
from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship

from app import db

class TrombiAdmin(db.Model):
    __tablename__ = 'trombi_admin'
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(80), unique=True)
    password = db.Column(db.String(64))

    # Flask-Login integration
    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.id

    # Required for administrative interface
    def __unicode__(self):
        return self.login

class Team(db.Model):
    __tablename__ = 'team'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=False)

    persons = relationship("Person", backref="team")
    team_id = Column(Integer, ForeignKey('team.id'))
    high_team = relationship("Team", backref="sub_teams", remote_side="Team.id")

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return self.name

    # The root persons of a team are the persons who's boss
    # is in a different team (or no boss)
    def get_root_persons(self):
        print(self.persons)
        root_persons = []
        for person in self.persons:
            print(person)
            if ((person.manager is None) or (person.manager.team_id != self.id)):
                root_persons.append(person)
        return root_persons


class Person(db.Model):
    __tablename__ = 'person'
    # service;login;nom;prenom;naissance;poste;mail;skype;fixe;portable;manager
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(80), unique=False)
    name = db.Column(db.String(80), unique=False)
    surname = db.Column(db.String(80), unique=False)
    birthday = db.Column(db.Date, unique=False)
    arrival = db.Column(db.Date, unique=False)
    email = db.Column(db.String(120), unique=False)
    mobile = db.Column(db.String(120), unique=False)
    fixe = db.Column(db.String(120), unique=False)
    job = db.Column(db.String(120), unique=False)
    skype = db.Column(db.String(120), unique=False)

    manager_id = Column(Integer, ForeignKey('person.id'))
    manager = relationship("Person", backref="subordinates", remote_side="Person.id")

    team_id = Column(Integer, ForeignKey('team.id'))

    def __repr__(self):
        return self.skype

    def get_number_of_years(self):
        return self.arrival

    def get_arrival_date(self):
        return datetime.datetime.fromtimestamp(float(self.arrival))

    def get_pretty_arrival_date(self):
        return self.arrival.strftime('Arrived %B, %d %Y')

    def get_pretty_birthday_date(self):
        return self.birthday.strftime('Born %B, %d')


class Trivia(db.Model):
    __tablename__ = 'trivia'
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text(), unique=False, default=u'Hello World!')
