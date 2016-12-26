"""Models for the trombi."""
import datetime
from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship

from app import db


class TrombiAdmin(db.Model):
    """
    Represents the administrator of the trombi.

    It's the only one that has access to the admin panel.
    """

    __tablename__ = 'trombi_admin'
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(80), unique=True)
    password = db.Column(db.String(64))

    # Flask-Login integration
    def is_authenticated(self):
        """Check if the admin is authenticated."""
        return True

    def is_active(self):
        """Check if the admin is active."""
        return True

    def is_anonymous(self):
        """Check if the admin is anonymous."""
        return False

    def get_id(self):
        """Get the admin's ID."""
        return self.id

    def __unicode__(self):
        """Required for administrative interface."""
        return self.login


class Team(db.Model):
    """Represents a team in the trombi."""

    __tablename__ = 'team'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=False)

    persons = relationship("Person", backref="team")

    team_id = Column(Integer, ForeignKey('team.id'))
    high_team = relationship(
            "Team",
            backref="sub_teams",
            remote_side="Team.id"
        )

    def __init__(self, name):
        """Simple constructor."""
        self.name = name

    def __repr__(self):
        """Simple log method."""
        return self.name

    def get_root_persons(self):
        """
        Get the manager of the team.

        The root persons of a team are the persons who's boss is in a different
        team (or no boss).
        """
        root_persons = []
        for person in self.persons:
            if (person.manager is None or person.manager.team_id != self.id):
                root_persons.append(person)
        return root_persons


class Person(db.Model):
    """Represents a person in the trombi."""

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
    manager = relationship(
        "Person",
        backref="subordinates",
        remote_side="Person.id"
    )

    team_id = Column(Integer, ForeignKey('team.id'))

    def __repr__(self):
        """Simple log method."""
        return self.skype

    def get_arrival_date(self):
        """Get the date when the person arrived."""
        return datetime.datetime.fromtimestamp(float(self.arrival))

    def get_pretty_arrival_date(self):
        """Get a printable version of the arrival date."""
        return self.arrival.strftime('Arrived %B, %d %Y')

    def get_pretty_birthday_date(self):
        """Get a printable version of the birthday date."""
        return self.birthday.strftime('Born %B, %d')


class Trivia(db.Model):
    """Represents the content of the trivia page."""

    __tablename__ = 'trivia'
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text(), unique=False, default=u'Hello World!')
