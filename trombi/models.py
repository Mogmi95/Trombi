"""Models for the trombi."""
import datetime
import time
from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from flask_babel import gettext

from .app import db


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
        return str(self.login)


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

    def __init__(self, name=""):
        """Simple constructor."""
        self.name = name

    def __repr__(self):
        """Simple log method."""
        return str(self.name)

    def as_dict(self):
        """Dumps the data as JSON"""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

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


class PersonComment(db.Model):
    """Comment on a person information."""

    def __repr__(self):
        """Simple log method."""
        return str(self.message)

    __tablename__ = 'personcomment'
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.String(512), unique=False)
    pending_room_id = db.Column(db.Integer, unique=False)

    person_id = Column(Integer, ForeignKey('person.id'))


class Person(db.Model):
    """Represents a person in the trombi."""

    def as_dict(self):
        """Dumps the data as JSON"""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    __tablename__ = 'person'
    # service;login;nom;prenom;naissance;poste;mail;skype;fixe;portable;manager
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(80), unique=False)
    name = db.Column(db.String(80), unique=False)
    surname = db.Column(db.String(80), unique=False)
    birthday = db.Column(db.DateTime, unique=False, server_default=func.now())
    arrival = db.Column(db.DateTime, unique=False, server_default=func.now())
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

    room_id = Column(Integer, ForeignKey('room.id'))

    comments = relationship("PersonComment", backref="person")

    def __repr__(self):
        """Simple log method."""
        return str(self.login)

    def get_pretty_arrival_date(self):
        """Get a printable version of the arrival date."""
        now = datetime.datetime.now()
        diff = now - self.arrival
        custom_date = self.arrival.strftime(u'%Y/%m/%d')

        years = diff.days // 365
        months = (diff.days % 365) // 30

        return gettext(
            u'%(date)s (%(y)s years, %(m)s months)',
            date=custom_date,
            y=years,
            m=months,
        )

    def get_arrival_date_timestamp(self):
        """Get an epoch timestamp of the arrival date"""
        d = int(time.mktime(self.arrival.timetuple()))
        if (d <= 0):
            return 0
        else:
            return d

    def get_birthday_date_timestamp(self):
        """Get an epoch timestamp of the birthday date"""
        d = int(time.mktime(self.birthday.timetuple()))
        if (d <= 0):
            return 0
        else:
            return d

    def get_pretty_birthday_date(self):
        """Get a printable version of the birthday date."""
        custom_date = self.birthday.strftime(u'%B, %d')
        return gettext(u'%(date)s', date=custom_date)

    def create_vcard(self):
        """Create a VCard for a person."""
        vcard = \
            'BEGIN:VCARD\n'\
            'VERSION:3.0\n'\
            'N:{};{}\n'\
            'FN:{} {}\n'\
            'TITLE:{}\n'\
            'TEL;TYPE=WORK,VOICE:{}\n'\
            'EMAIL;TYPE=PREF,INTERNET:{}\n'\
            'END:VCARD'.format(
                self.surname,
                self.name,
                self.name,
                self.surname,
                self.job,
                self.mobile,
                self.email
            )
        return vcard


class Infos(db.Model):
    """Represents the content of the infos page."""

    def __str__(self):
        """Simple log method."""
        return str(id)

    def as_dict(self):
        """Dumps the data as JSON"""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    __tablename__ = 'infos'
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text(), unique=False, default=u'Hello World!')


class LinkCategory(db.Model):
    """Represents a category of links."""

    def __str__(self):
        """Simple log method."""
        return str(self.title)

    def as_dict(self):
        """Dumps the data as JSON"""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    __tablename__ = "link_category"
    id = db.Column(db.Integer, primary_key=True)
    order = db.Column(db.Integer, unique=False)
    image = db.Column(db.Text(), unique=False)
    title = db.Column(db.Text(), unique=False, default=u'Title')
    description = db.Column(db.Text(), unique=False, default=u'Description')

    links = relationship("Link", backref="category")


class Link(db.Model):
    """Represents an interesting link."""

    def __str__(self):
        """Simple log method."""
        return str(self.title)

    def as_dict(self):
        """Dumps the data as JSON"""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    __tablename__ = 'links'
    id = db.Column(db.Integer, primary_key=True)
    order = db.Column(db.Integer, unique=False)
    url = db.Column(db.Text(), unique=False)
    image = db.Column(db.Text(), unique=False)
    title = db.Column(db.Text(), unique=False, default=u'Title')
    description = db.Column(db.Text(), unique=False, default=u'Description')
    category_id = Column(Integer, ForeignKey('link_category.id'))


class Room(db.Model):
    """Represents a Room containing Persons."""

    def __str__(self):
        """Simple log method."""
        return str(self.name)

    def as_dict(self):
        """Dumps the data as JSON"""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    __tablename__ = 'room'
    id = db.Column(db.Integer, primary_key=True)
    identifier = db.Column(db.Text(), unique=False, default=u'ID')
    name = db.Column(db.Text(), unique=False, default=u'Room')
    is_for_meetings = db.Column(db.Boolean(), unique=False, default=False)
    coordinate_x = db.Column(db.Float, unique=False, default=0)
    coordinate_y = db.Column(db.Float, unique=False, default=0)

    floor_id = Column(Integer, ForeignKey('floor.id'))

    persons = relationship("Person", backref="room")


class Floor(db.Model):
    """Represents a Floor containing Rooms."""

    def __str__(self):
        """Simple log method."""
        return str(self.name)

    def as_dict(self):
        """Dumps the data as JSON"""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    __tablename__ = 'floor'
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(80), unique=True)
    name = db.Column(db.Text(), unique=False, default=u'Floor')

    rooms = relationship("Room", backref="floor")