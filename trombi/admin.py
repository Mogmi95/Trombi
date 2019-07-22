"""Administration panel."""
from os import listdir, mkdir
from os.path import isdir
from shutil import copy
import time
import datetime
import io
import os
import csv

from flask import request, url_for, redirect
from wtforms import form, fields, validators
from wtforms.widgets import TextArea
from wtforms.fields import TextAreaField
from flask_admin.contrib import sqla
from flask_admin import helpers, expose, BaseView
from flask_admin.form.upload import FileUploadField
import flask_admin as flask_admin
import flask_login as login
import json
from werkzeug.security import check_password_hash

from .models import TrombiAdmin, Person, PersonComment, Team, Infos, Link, Room, Floor
from .app import db, app
import config


class LoginForm(form.Form):
    """Define login and registration forms (for flask-login)."""

    login = fields.StringField(u'Login', validators=[validators.required()])
    password = fields.PasswordField(
        u'Password',
        validators=[validators.required()]
    )

    def validate_login(self, field):
        """Check if the user is administrator."""
        user = self.get_user()

        if user is None:
            raise validators.ValidationError('Invalid user')

        if not check_password_hash(user.password, self.password.data):
            raise validators.ValidationError('Invalid password')

    def get_user(self):
        """Get the admin from the database."""
        return db.session.query(TrombiAdmin).filter_by(
            login=self.login.data
        ).first()


def init_login():
    """Initialize flask-login."""
    login_manager = login.LoginManager()
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        """Create user loader function."""
        return db.session.query(TrombiAdmin).get(user_id)


class MyAdminIndexView(flask_admin.AdminIndexView):
    """Create customized view class that handles login & registration."""

    @expose('/')
    def index(self):
        """The root of the admin panel."""
        if not login.current_user.is_authenticated:
            return redirect(url_for('.login_view'))
        return super(MyAdminIndexView, self).index()

    @expose('/login/', methods=('GET', 'POST'))
    def login_view(self):
        """Handle user login."""
        form = LoginForm(request.form)
        if helpers.validate_form_on_submit(form):
            user = form.get_user()
            login.login_user(user)

        if login.current_user.is_authenticated:
            return redirect(url_for('.index'))
        self._template_args['form'] = form
        return super(MyAdminIndexView, self).index()

    @expose('/logout/')
    def logout_view(self):
        """Handle user logout."""
        login.logout_user()
        return redirect(url_for('.index'))


class CKEditorWidget(TextArea):
    """A custom text editor for the admin panel."""

    def __call__(self, field, **kwargs):
        """Declare the text editor."""
        if kwargs.get('class'):
            kwargs['class'] += " ckeditor"
        else:
            kwargs.setdefault('class', 'ckeditor')
        return super(CKEditorWidget, self).__call__(field, **kwargs)


class CKEditorField(TextAreaField):
    """A custom text editor for the admin panel."""

    widget = CKEditorWidget()

# TODO : Rename MyModelView


class MyModelView(sqla.ModelView):
    """Create customized model view class."""

    def is_accessible(self):
        """Check if the current user can access the view."""
        return login.current_user.is_authenticated
    # Change edit in the admin
    form_overrides = dict(text=CKEditorField)
    can_view_details = True
    create_template = 'admin/edit.html'
    edit_template = 'admin/edit.html'
    column_searchable_list = ['id']

class PersonView(sqla.ModelView):
    """Create customized model view class."""
    edit_template = 'admin/person_edit.html'
    # Change edit in the admin
    can_view_details = True
    column_searchable_list = ['login', 'name', 'surname']
    form_columns = ('login', 'photo', 'name', 'surname', 'team', 'manager','birthday', 'arrival', 'email', 'mobile', 'fixe', 'job', 'skype', 'subordinates', 'room')

    def is_accessible(self):
        """Check if the current user can access the view."""
        return login.current_user.is_authenticated

    def image_name(self, file_data):
        """Return the name of the image for a person."""
        return self.login + ".jpg"

    form_extra_fields = {
        'photo': FileUploadField('Photo',
                                base_path=config.PHOTOS_FOLDER,
                                namegen=image_name,)
    }


# Maps edition
class MapsView(BaseView):
    """Allow the administration of maps"""

    def is_accessible(self):
        return login.current_user.is_authenticated

    @expose('/test', methods=['POST'])
    def test(self):
        selected_floor_id = request.form.get('floorId')
        data = request.form.get('data')
        parsedData = json.loads(data)

        print(parsedData)
        for elt in parsedData:
            roomId = elt['id']
            x = elt['x']
            y = elt['y']
            room = Room.query.filter_by(id=roomId).first()
            room.coordinate_x = x
            room.coordinate_y = y
            db.session.add(room)
        db.session.commit()
        return str(data)

    @expose('/', methods=['GET', 'POST'])
    def get_view(self):
        """Display the available maps operations."""

        floors = Floor.query.all()
        
        selected_floor_id = request.args.get('floor')
        selected_floor = None
        if (selected_floor_id is not None):
            selected_floor_id = int(selected_floor_id)
            for f in floors:
                if f.id == selected_floor_id:
                    selected_floor = f

        
        superjson = '['
        if selected_floor is not None:
            jsonformat = u'{{ "id": "{}", "name": "{}", "x": "{}", "y": "{}" }},'
            for i, room in enumerate(selected_floor.rooms):
                if (i == len(selected_floor.rooms) - 1):
                    jsonformat = jsonformat[:-1]
                superjson += jsonformat.format(
                        room.id,
                        room.name,
                        room.coordinate_x,
                        room.coordinate_y,
                    )
        superjson += ']'
        
        return self.render(
            'admin/maps.html',
            floors=floors,
            selected_floor=selected_floor,
            superjson=superjson
        )


class DatetimeEncoder(json.JSONEncoder):
    """Custom datetime.datetime JSON encoder because it is not serializable anymore."""

    def default(self, o):
        if isinstance(o, datetime.datetime):
            return o.isoformat()

        return super().default(self, o)


# Database backup
class DatabaseSaveView(BaseView):
    """Expose a way to backup/load the database."""

    def is_accessible(self):
        """Check if the current user can access the view."""
        return login.current_user.is_authenticated

    @expose('/load_backuped_database', methods=['POST'])
    def load_backuped_database(self):
        """Load a backuped version of the database."""
        filename = request.form.get('saves_select')
        if (filename is not None):
            copy(str(config.DATABASE_SAVES_DIRECTORY + '/' + filename), config.DATABASE_PATH)
        return redirect(url_for('database.get_view'))

    @expose('/import_json', methods=['POST'])
    def load_json(self):
        """We create the persons from a JSON file."""

        # check if the post request has the file part
        if 'json_file' not in request.files:
            return redirect(url_for('database.get_view', error='Missing JSON file'))
        file = request.files['json_file']
        # if user does not select file, browser also
        # submit a empty part without filename
        if file.filename == '':
            return redirect(url_for('database.get_view', error='Missing JSON file'))
        if file:
            file.save(os.path.join(config.JSON_FOLDER, 'database.json'))

        # Cleaning the existing data. This change is not registered until the parsing is ok
        # db.session.query(Person).delete()
        # db.session.query(Team).delete()

        #try:
        with io.open(os.path.join(config.JSON_FOLDER, 'database.json'), 'r', encoding='utf8') as f:
            data = json.load(f)

            # TEAMS
            print(data['teams'])
            teams = {}
            for team_json in data['teams']:
                neo_team = Team()
                team_id = team_json['id']
                neo_team.name = team_json['name']
                teams[team_id] = neo_team
                db.session.add(neo_team)

            # PERSONS
            managers = {}
            persons = {}
            # We create all the persons and store a map with their ID
            for person_json in data['persons']:
                neo_person = Person()
                person_id = person_json['id']
                neo_person.login = person_json['login']
                neo_person.name = person_json['name']
                neo_person.surname = person_json['surname']
                neo_person.birthday =  datetime.datetime.strptime(person_json['birthday'], '%Y-%m-%d %H:%M:%S')
                neo_person.arrival =  datetime.datetime.strptime(person_json['arrival'], '%Y-%m-%d %H:%M:%S')
                neo_person.email = person_json['email']
                neo_person.mobile = person_json['mobile']
                neo_person.fixe = person_json['fixe']
                neo_person.job = person_json['job']
                neo_person.skype = person_json['skype']
                
                person_team_id = person_json['team_id']
                if (person_team_id == 'None'):
                    print('Warning : ' + neo_person.login + ' has no team !')
                else:
                    neo_person.team = teams[person_json['team_id']]
                persons[person_id] = neo_person
                # We store data about the managers
                manager = person_json['manager_id']
                if manager in managers:
                    managers[manager].append(neo_person)
                else:
                    managers[manager] = [neo_person]
                db.session.add(neo_person)

            # We create the link between persons and managers
            for manager_id, managed_persons in managers.items():
                if manager_id in persons:
                    manager = persons[manager_id]
                    for managed_person in managed_persons:
                        managed_person.manager = manager
                else:
                    print('Missing a manager: ' + manager_id)

            # LINKS
            for link_json in data['links']:
                neo_link = Link()
                neo_link.order = link_json['order']
                neo_link.url = link_json['url']
                neo_link.image = link_json['image']
                neo_link.title = link_json['title']
                neo_link.description = link_json['description']
                db.session.add(neo_link)

            # INFOS
            for info_json in data['infos']:
                print(info_json)
                neo_info = Infos()
                neo_info.text = info_json['text']
                db.session.add(neo_info)

            db.session.commit()
            return str(teams)
        #except:
            #return redirect(url_for('database.get_view', error='Error while parsing JSON. Check logs.'))

    @expose('/import_csv', methods=['POST'])
    def load_csv(self):
        """We create the persons from the data files."""

        # check if the post request has the file part
        if 'csv_file' not in request.files:
            return redirect(url_for('database.get_view', error='Missing file'))
        file = request.files['csv_file']
        # if user does not select file, browser also
        # submit a empty part without filename
        if file.filename == '':
            return redirect(url_for('database.get_view', error='Missing file'))
        if file:
            file.save(os.path.join(config.CSV_FOLDER, 'persons.csv'))

        # Cleaning the existing data. This change is not registered until the parsing is ok
        db.session.query(Person).delete()
        db.session.query(Team).delete()

        # Parsing the CSV file
        persons = []
        managers = {}
        existing_teams = {}

        try:
            with io.open(os.path.join(config.CSV_FOLDER, 'persons.csv'), 'r', encoding='utf8') as f:
                reader = csv.reader(f, delimiter=',', quotechar='"')
                for row in reader:
                    if (len(row) > 1):
                        neo = Person()

                        neo.login = row[1].strip().lower()
                        neo.surname = row[2]
                        neo.name = row[3]
                        neo.birthday = datetime.datetime.fromtimestamp(
                            float(self.format_date(row[4]))
                        )
                        neo.arrival = datetime.datetime.fromtimestamp(
                            float(self.format_date(row[5]))
                        )
                        neo.job = row[6]
                        neo.email = row[7]
                        neo.skype = row[8]
                        neo.fixe = row[9]
                        neo.mobile = row[10]

                        # TEAM
                        team = row[0]
                        if not (team in existing_teams):
                            print('Creating team ' + team + ' for ' + neo.login)
                            neo_team = Team(team)
                            existing_teams[team] = neo_team
                            db.session.add(neo_team)
                        neo.team = existing_teams[team]

                        # MANAGER
                        manager = row[11]
                        if manager in managers:
                            managers[manager].append(neo)
                        else:
                            managers[manager] = [neo]

                        persons.append(neo)

            # We have to commit here first to create Team links
            # TODO : Add check on the persons here (ex: detect loops)
            db.session.commit()

            for person in persons:
                # We link the managers
                if person.login in managers:
                    person.subordinates = managers[person.login]
                    # We create a team hierarchy
                    for subperson in person.subordinates:
                        if (subperson.team_id != person.team_id):
                            subperson.team.high_team = person.team
                db.session.add(person)

            db.session.commit()
        except csv.Error as e:
            return redirect(url_for('database.get_view', error=e))
        except:
            return redirect(url_for('database.get_view', error='Error while parsing. Check logs.'))
        
        return redirect(url_for('database.get_view', error=None))


    def format_date(self, date):
        """Parse the date from the data file."""
        if (date is None or date == ''):
            return 0

        try:
            if (len(date.split('/')) == 3):
                return time.mktime(
                    datetime.datetime.strptime(date, u"%Y/%m/%d").timetuple()
                    )
            else:
                return time.mktime(
                    datetime.datetime.strptime(date, "%d/%m").timetuple()
                    )
        except:
            print('Cannot convert : ' + date)
            return 0

        return ''

    @expose('/trombi_database.json', methods=['GET'])
    def create_database_backup_json(self):
        """Create a backup of the current database in JSON."""

        TO_DUMP = [
            (Person, 'persons'),
            (Team, 'teams'),
            (Infos, 'infos'),
            (Link, 'links'),
        ]

        result = {}

        for elt in TO_DUMP:
            current_class = elt[0]
            current_id = elt[1]
            tmp_elts = current_class.query.all()
            result[current_id] = []
            for item in tmp_elts:
                result[current_id].append(item.as_dict())

        return json.dumps(result, cls=DatetimeEncoder)

    @expose('/trombi_database.csv', methods=['GET'])
    def create_database_backup(self):
        """Create a backup of the current database."""
        filename = datetime.datetime.now().isoformat()
        filename += ".csv"

        header = "#TEAM,LOGIN,NOM,PRENOM,NAISSANCE,ARRIVEE,FONCTION,MAIL,SKYPE,FIXE,PORTABLE,MANAGER,ROOM"

        output = io.StringIO()
        writer = csv.writer(
            output,
            quoting=csv.QUOTE_ALL,
            delimiter=',')
        writer.writerow([header])

        persons = Person.query.all()
        for person in persons:
            writer.writerow([
                '' if (person.team == None) else person.team.name.encode('utf-8'),
                '' if (person.login == None) else person.login.encode('utf-8'),
                '' if (person.surname == None) else person.surname.encode('utf-8'),
                '' if (person.name == None) else person.name.encode('utf-8'),
                '1990/01/01' if (person.birthday == None) else person.birthday.strftime(u'%Y/%m/%d'),
                '1990/01/01' if (person.arrival == None) else person.arrival.strftime(u'%Y/%m/%d'),
                '' if (person.job == None) else person.job.encode('utf-8'),
                '' if (person.email == None) else person.email.encode('utf-8'),
                '' if (person.skype == None) else person.skype.encode('utf-8'),
                '' if (person.fixe == None) else person.fixe.encode('utf-8'),
                '' if (person.mobile == None) else person.mobile.encode('utf-8'),
                '' if (person.manager == None) else person.manager.login.encode('utf-8'),
                "room"
                ])


        return output.getvalue()

    @expose('/', methods=['GET', 'POST'])
    def get_view(self):
        """Display the available database operations."""
        # Getting the available database saves
        saves = listdir(config.DATABASE_SAVES_DIRECTORY)
        saves.sort()
        saves.reverse()
        return self.render(
            'admin/database.html',
            available_saves=saves
        )


# Report information errors
class CommentsView(BaseView):
    """List the comments written by the users."""

    def is_accessible(self):
        """Check if the current user can access the view."""
        return login.current_user.is_authenticated

    @expose('/', methods=['GET'])
    def get_view(self):
        """Display the available comments."""
        comments = PersonComment.query.all()
        return self.render(
            'admin/comments.html',
            comments=comments
        )

    @expose('/delete/<comment_id>', methods=['GET', 'POST'])
    def delete_comment(self, comment_id=None):
        """Delete a comment."""
        comment = PersonComment.query.filter_by(id=comment_id).first()
        db.session.delete(comment)
        db.session.commit()
        return redirect(url_for('comments.get_view'))


    @expose('/accept/<comment_id>', methods=['GET', 'POST'])
    def accept_comment(self, comment_id=None):
        """Accept a comment."""
        comment = PersonComment.query.filter_by(id=comment_id).first()

        # If a room change has been requested, we move the rquested person to the new room
        new_room = Room.query.filter_by(id=comment.pending_room_id).first()
        comment.person.room = new_room

        db.session.add(comment.person)
        db.session.delete(comment)
        db.session.commit()
        return redirect(url_for('comments.get_view'))

# Display charts
class ChartsView(BaseView):
    """Display an exportable version of the teams."""

    def is_accessible(self):
        """Check if the current user can access the view."""
        return login.current_user.is_authenticated

    @expose('/', methods=['GET', 'POST'])
    def get_view(self):
        """Get the view."""
        selected_team = request.form.get('team_select')
        teams = Team.query.all()
        use_images = request.form.get('use_images') != None
        print(use_images)
        if selected_team is None:
            team = teams[0]
        else:
            team = Team.query.filter_by(id=selected_team).first()

        size = 2
        selected_size = request.form.get('size')
        if selected_size is not None:
            size = int(selected_size)

        leader = team.get_root_persons()[0]
        datasource = create_chart_node_for_person(leader, size)

        return self.render(
            'admin/charts.html',
            datasource=datasource,
            current_team=team,
            teams=teams,
            size=size,
            use_images=use_images,
        )

def create_chart_node_for_person(person, max_size):
    size = 0
    result = "{'name': '%s','title': '%s', 'login': '%s','children':[" % (person.name.replace('\'','\\\''), person.job.replace('\'','\\\''), person.login)
    if (size < max_size):
        size += 1
        for subordinate in person.subordinates:
            result += create_chart_node_for_person(subordinate, max_size - size) + ','
    result += ']}'
    return result;

def init():
    """Create the administration system."""
    # Initialize flask-login
    init_login()

    # Create admin
    admin = flask_admin.Admin(
        app,
        'Trombi admin',
        index_view=MyAdminIndexView(),
        base_template='admin/master.html'
    )

    # Add view

    # Do we want the admin to editate this ?
    # admin.add_view(MyModelView(TrombiAdmin, db.session))

    admin.add_view(PersonView(Person, db.session))
    admin.add_view(MyModelView(Team, db.session))
    admin.add_view(MyModelView(Infos, db.session))
    admin.add_view(MyModelView(Link, db.session))
    admin.add_view(MyModelView(Room, db.session))
    admin.add_view(MyModelView(Floor, db.session))
    admin.add_view(MapsView(name='Maps', endpoint='maps'))
    admin.add_view(DatabaseSaveView(name='Database', endpoint='database'))
    admin.add_view(ChartsView(name='Charts', endpoint='charts'))
    admin.add_view(CommentsView(name='Comments', endpoint='comments'))

    # We create the database backup directory if it doesn't exists
    if (not isdir(config.DATABASE_SAVES_DIRECTORY)):
        mkdir(config.DATABASE_SAVES_DIRECTORY)
        print('Backup directory created at ' + config.DATABASE_SAVES_DIRECTORY)
