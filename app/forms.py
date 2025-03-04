from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, FileField, SelectField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Length
import sqlalchemy as sa
from app import db
from app.models import User
import re


USERNAME_REGEX = r'^[a-zA-Z0-9_]+$'

def validate_username_format(form, field):
    """Custom validator for username format"""
    if not re.match(USERNAME_REGEX, field.data):
        raise ValidationError('Username must only contain letters, numbers, and underscores, with no spaces.')

class CreateGroupForm(FlaskForm):
    name = StringField('Group Name', validators=[DataRequired(), Length(min=3, max=100)])
    icon = FileField('Group Icon')
    description = TextAreaField('Description', validators=[DataRequired(), Length(min=10)])
    status = SelectField('Status', choices=[('public', 'Public'), ('private', 'Private')], validators=[DataRequired()])
    submit = SubmitField('Create Group')

class AddUserToGroupForm(FlaskForm):
    group_id = SelectField('Group', coerce=int, validators=[DataRequired()])
    user_id = SelectField('User', coerce=int, validators=[DataRequired()])
    role = SelectField('Role', choices=[('USER', 'User'), ('ADMIN', 'Admin'), ('OWNER', 'Owner')], validators=[DataRequired()])
    submit = SubmitField('Add User to Group')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Keep me logged in')
    submit = SubmitField('Sign In')

    def validate_username(self, field):
        field.data = field.data.strip()  # Removes leading & trailing spaces


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), validate_username_format, Length(min=0, max=25)])
    display_name = StringField('Username', validators=[DataRequired(), Length(min=0, max=25)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = db.session.scalar(sa.select(User).where(
            User.username == username.data))
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = db.session.scalar(sa.select(User).where(
            User.email == email.data))
        if user is not None:
            raise ValidationError('Please use a different email address.')
        
class EditProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), validate_username_format])
    about_me = TextAreaField('About me', validators=[Length(min=0, max=140)])
    submit = SubmitField('Submit')

    def __init__(self, original_username, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        if username.data != self.original_username:
            user = db.session.scalar(sa.select(User).where(
                User.username == username.data))

class EmptyForm(FlaskForm):
    submit = SubmitField('Submit')


class PostForm(FlaskForm):
    post = TextAreaField('Say something', validators=[DataRequired(), Length(min=1, max=1000)])
    tags = StringField('Tags (comma separated)', validators=[DataRequired(), Length(max=50)])
    submit = SubmitField('Submit')

class ResetPasswordRequestForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')


class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Request Password Reset')