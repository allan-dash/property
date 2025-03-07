from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, FileField, SelectField, IntegerField, DecimalField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo, Length, Optional
from wtforms_sqlalchemy.fields import QuerySelectMultipleField
import sqlalchemy as sa
from app import db
from app.models import User, Amenity
import re

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Keep me logged in')
    submit = SubmitField('Sign In')


class AddPropertyForm(FlaskForm):
    name = StringField('Property Name', validators=[DataRequired()])
    location = StringField('Location', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[Optional()])
    bedrooms = IntegerField('Bedrooms', validators=[DataRequired()])
    bathrooms = DecimalField('Bathrooms', places=1, validators=[DataRequired()])
    beds = IntegerField('Beds', validators=[DataRequired()])
    guests = IntegerField('Guest Capacity', validators=[DataRequired()])
    size = IntegerField('Size (sqft)', validators=[DataRequired()])
    price = DecimalField('Price per Night ($)', places=2, validators=[DataRequired()])
    latitude = StringField('Latitude', validators=[Optional()])
    longitude = StringField('Longitude', validators=[Optional()])
    submit = SubmitField('Add Property')

class RegistrationForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    firstname = StringField('First Name', validators=[DataRequired()])
    lastname = StringField('Last Name', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

class AddAmenityForm(FlaskForm):
    name = StringField('Amenity Name', validators=[DataRequired()])
    icon = StringField('Icon (FontAwesome/Material UI class)', validators=[DataRequired()])
    submit = SubmitField('Add Amenity')

    def validate_email(self, email):
        user = db.session.scalar(sa.select(User).where(
            User.email == email.data))
        if user is not None:
            raise ValidationError('Please use a different email address.')
        
        
class AddAmenitiesToPropertyForm(FlaskForm):
    amenities = QuerySelectMultipleField(
        'Amenities',
        query_factory=None,  # We'll set this dynamically in the view
        get_label='name',
        allow_blank=True
    )
    submit = SubmitField('Submit')

    def __init__(self, *args, **kwargs):
        property_instance = kwargs.pop('property_instance', None)
        super(AddAmenitiesToPropertyForm, self).__init__(*args, **kwargs)
        
        if property_instance:
            # Dynamically set the query_factory based on the property_instance
            self.amenities.query_factory = lambda: Amenity.query.filter(
                Amenity.id.notin_([a.id for a in property_instance.amenities])
            ).all()



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