import flask
import flask.ext.sqlalchemy
from flask import render_template
from sqlalchemy.orm import relationship, backref
from sqlalchemy import Table, Column, Integer, ForeignKey

database_url = 'sqlite:////home/mogmi/Prog/web/Trombi/test.db'


# Create the Flask application and the Flask-SQLAlchemy object.
app = flask.Flask(__name__, static_url_path='/static')
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
db = flask.ext.sqlalchemy.SQLAlchemy(app)

class Team(db.Model):
    __tablename__ = 'team'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=False)
    persons = relationship("Person", backref="parent")

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return 'Team(' + str(self.id) + ')=' + self.name

class Person(db.Model):
    __tablename__ = 'person'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=False)
    email = db.Column(db.String(120), unique=False)
    job = db.Column(db.String(120), unique=False)
    team_id = Column(Integer, ForeignKey('team.id'))
    skype = db.Column(db.String(120), unique=False)

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return 'Person(' + str(self.id) + ')=' + self.name

@app.route("/")
def main():
    teams = Team.query.all()
    return render_template('index.html', teams=teams)

@app.route('/ajax/createPerson/<id>')
def command(id=None):
    print('Creating a person in team : ' + str(id))

    team = Team.query.filter_by(id=id).first()
    print('Team : ' + str(team))

    person = Person('PERSON')

    team.persons.append(person)
    db.session.commit()

    print('Person : ' + str(person))

    return str(person.id)

if __name__ == "__main__":
    db.create_all()

    #team = Team('Team test');
    #db.session.add(team)
    #db.session.commit()

    app.run()
