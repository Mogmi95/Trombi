"""Administration panel."""
from os import listdir, mkdir
from os.path import isdir
from shutil import copy
from datetime import datetime
import io
import csv

from flask import request, url_for, redirect
from wtforms import form, fields, validators
from wtforms.widgets import TextArea
from wtforms.fields import TextAreaField
from flask_admin.contrib import sqla
from flask_admin import helpers, expose, BaseView
import flask_admin as flask_admin
import flask_login as login
from werkzeug.security import check_password_hash

from models import TrombiAdmin, Person, PersonComment, Team, Infos
from app import db, app
from config import DATABASE_SAVES_DIRECTORY, DATABASE_PATH


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
    create_template = 'edit.html'
    edit_template = 'edit.html'
    column_searchable_list = ['id']

class PersonView(sqla.ModelView):
    """Create customized model view class."""

    def is_accessible(self):
        """Check if the current user can access the view."""
        return login.current_user.is_authenticated
    # Change edit in the admin
    can_view_details = True
    column_searchable_list = ['login', 'name', 'surname']


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
            copy(str(DATABASE_SAVES_DIRECTORY + '/' + filename), DATABASE_PATH)
        return redirect(url_for('database.get_view'))

    @expose('/trombi_database.csv', methods=['GET'])
    def create_database_backup(self):
        """Create a backup of the current database."""
        filename = datetime.now().isoformat()
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
        saves = listdir(DATABASE_SAVES_DIRECTORY)
        saves.sort()
        saves.reverse()
        return self.render(
            'database.html',
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
        print('lolzcomments : ' + str(comments))
        return self.render(
            'comments.html',
            comments=comments
        )

    @expose('/delete/<comment_id>', methods=['GET', 'POST'])
    def delete_comment(self, comment_id=None):
        """Delete a comment."""
        comment = PersonComment.query.filter_by(id=comment_id).first()
        db.session.delete(comment)
        db.session.commit()
        return redirect(url_for('comments.get_view'))


def init():
    """Create the administration system."""
    # Initialize flask-login
    init_login()

    # Create admin
    admin = flask_admin.Admin(
        app,
        'Trombi admin',
        index_view=MyAdminIndexView(),
        base_template='master.html'
    )

    # Add view

    # Do we want the admin to editate this ?
    # admin.add_view(MyModelView(TrombiAdmin, db.session))

    admin.add_view(PersonView(Person, db.session))
    admin.add_view(MyModelView(Team, db.session))
    admin.add_view(MyModelView(Infos, db.session))
    admin.add_view(DatabaseSaveView(name='Database', endpoint='database'))
    admin.add_view(CommentsView(name='Comments', endpoint='comments'))

    # We create the database backup directory if it doesn't exists
    if (not isdir(DATABASE_SAVES_DIRECTORY)):
        mkdir(DATABASE_SAVES_DIRECTORY)
        print('Backup directory created at ' + DATABASE_SAVES_DIRECTORY)
