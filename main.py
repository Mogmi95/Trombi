import flask
import flask.ext.sqlalchemy
from flask import render_template, redirect
from sqlalchemy.orm import relationship, backref
from sqlalchemy import Table, Column, Integer, ForeignKey
from flask.ext.wtf import Form
from wtforms import StringField, BooleanField, HiddenField
from wtforms.validators import DataRequired

'''
    INIT
'''

# Create the Flask application and the Flask-SQLAlchemy object.
app = flask.Flask(__name__, static_url_path='/static')
app.config.from_object('config')

db = flask.ext.sqlalchemy.SQLAlchemy(app)

'''
    TABLES
'''

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
    image = db.Column(db.String(120), unique=False)
    email = db.Column(db.String(120), unique=False)
    phone = db.Column(db.String(120), unique=False)
    job = db.Column(db.String(120), unique=False)
    skype = db.Column(db.String(120), unique=False)
    team_id = Column(Integer, ForeignKey('team.id'))

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return 'Person(' + str(self.id) + ')=' + self.name

'''
    MAIN
'''

@app.route("/")
def main():
    teams = Team.query.all()
    return render_template('index.html', teams=teams)

@app.route('/ajax/createPerson/<id>')
def create_person(id=None):
    print('Creating a person in team : ' + str(id))

    team = Team.query.filter_by(id=id).first()
    print('Team : ' + str(team))

    person = Person('PERSON')

    team.persons.append(person)
    db.session.commit()

    print('Person : ' + str(person))

    return str(person.id)


'''
    EDIT
'''

class EditForm(Form):
    person_id = HiddenField("PERSON_ID")
    name = StringField('name', default=None)
    # image = db.Column(db.String(120), unique=False)
    email = StringField('email', default=None)
    phone = StringField('phone', default=None)
    job = StringField('job', default=None)
    skype = StringField('skype', default=None)


@app.route('/ajax/showEdit/<person_id>')
def show_edit(person_id=None):
    print('Editing a person person_id : ' + str(person_id))
    person = Person.query.filter_by(id=person_id).first()
    form = EditForm(person_id=person_id,name=person.name, email=person.email, phone=person.phone, job=person.job, skype=person.skype)
    return render_template('form_module.html', person=person, form=form)

@app.route('/editPerson', methods=['GET', 'POST'])
def modify_person():
    form = EditForm()
    if form.validate_on_submit():
        person_id = form.person_id.data
        print("person_id : " + person_id)

        person = Person.query.filter_by(id=person_id).first()
        person.name = form.name.data
        person.email = form.email.data
        person.phone = form.phone.data
        person.job = form.job.data
        person.skype = form.skype.data
        db.session.commit()

        return redirect('/')


if __name__ == "__main__":
    db.create_all()

    #team = Team('Team test');
    #db.session.add(team)
    #db.session.commit()

    app.run()
