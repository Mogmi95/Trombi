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
from werkzeug.security import check_password_hash

from models import TrombiAdmin, Person, PersonComment, Team, Infos
from app import db, app
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
    form_columns = ('photo', 'login', 'name', 'surname', 'team', 'manager','birthday', 'arrival', 'email', 'mobile', 'fixe', 'job', 'skype')

    def is_accessible(self):
        """Check if the current user can access the view."""
        return login.current_user.is_authenticated

    def image_name(obj, file_data):
        return obj.login + ".jpg"

    form_extra_fields = {
        'photo': FileUploadField('Photo',
                                base_path=config.PHOTOS_FOLDER,
                                namegen=image_name,)
    }



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


    @expose('/trombi_database.csv', methods=['GET'])
    def create_database_backup(self):
        """Create a backup of the current database."""
        filename = datetime.datetime.now().isoformat()
        filename += ".csv"

        header = "#TEAM,LOGIN,NOM,PRENOM,NAISSANCE,ARRIVEE,FONCTION,MAIL,SKYPE,FIXE,PORTABLE,MANAGER,ROOM"

        output = io.BytesIO()
        writer = csv.writer(
            output,
            quoting=csv.QUOTE_ALL,
            delimiter=',')
        writer.writerow([header])

        persons = Person.query.all()
        for person in persons:
            writer.writerow([
                person.team,
                person.login,
                person.surname,
                person.name,
                person.birthday.strftime(u'%Y/%m/%d'),
                person.arrival.strftime(u'%Y/%m/%d'),
                person.job,
                person.email,
                person.skype,
                person.fixe,
                person.mobile,
                person.manager,
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

    @expose('/', methods=['GET', 'POST'])
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
    admin.add_view(DatabaseSaveView(name='Database', endpoint='database'))
    admin.add_view(ChartsView(name='Charts', endpoint='charts'))
    admin.add_view(CommentsView(name='Comments', endpoint='comments'))

    # We create the database backup directory if it doesn't exists
    if (not isdir(config.DATABASE_SAVES_DIRECTORY)):
        mkdir(config.DATABASE_SAVES_DIRECTORY)
        print('Backup directory created at ' + config.DATABASE_SAVES_DIRECTORY)
