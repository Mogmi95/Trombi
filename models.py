import datetime
from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship

from app import db

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

    def get_manager(self):
        print(self.persons)
        # The manager of a team is the person who's boss is in a different team (or no boss)
        for person in self.persons:
            print(person)
            if ((person.manager is None) or (person.manager.team_id != self.id)):
                return person


class Person(db.Model):
    __tablename__ = 'person'
    # service;login;nom;prenom;naissance;poste;mail;skype;fixe;portable;manager
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(80), unique=False)
    name = db.Column(db.String(80), unique=False)
    surname = db.Column(db.String(80), unique=False)
    birthday = db.Column(db.Integer, unique=False)
    arrival = db.Column(db.Integer, unique=False)
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

    def get_birthday_date(self):
        return datetime.datetime.fromtimestamp(float(self.birthday))
