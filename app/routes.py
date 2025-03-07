from flask import render_template, flash, redirect, url_for, request, Flask, jsonify
import logging
from app import app, db
from app.forms import LoginForm, RegistrationForm,ResetPasswordRequestForm, ResetPasswordForm, AddPropertyForm, AddAmenityForm, AddAmenitiesToPropertyForm
from flask_login import current_user, login_user, logout_user, login_required
import sqlalchemy as sa
from app.models import User, Property, Amenity
from urllib.parse import urlsplit
from datetime import datetime, timezone
from app.email import send_password_reset_email
from sqlalchemy import func
from werkzeug.utils import secure_filename
from sqlalchemy.orm import joinedload
import os
from flask import send_from_directory
import random
from functools import wraps

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}



logging.basicConfig(filename='flask_debug.log', level=logging.DEBUG)



def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'administrator':
            flash("You do not have permission to access this page.", "danger")
            return redirect(url_for('index'))  # Redirect non-admins
        return f(*args, **kwargs)
    return decorated_function


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def index():
    user = None
    if current_user.is_authenticated:
        user = db.first_or_404(sa.select(User).where(User.email == current_user.email))
    properties = Property.query.all()
    return render_template('index.html', title='Home', user=user, properties=properties)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.scalar(
            sa.select(User).where(func.lower(User.email) == form.email.data.lower()))
        if user is None or not user.check_password(form.password.data):
            flash('Invalid email or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or urlsplit(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = db.session.scalar(
            sa.select(User).where(User.email == form.email.data))
        if user:
            send_password_reset_email(user)
        flash('Check your email for the instructions to reset your password')
        return redirect(url_for('login'))
    return render_template('reset_password_request.html',
                           title='Reset Password', form=form)


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset.')
        return redirect(url_for('login'))
    return render_template('reset_password.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data,firstname=form.firstname.data,lastname=form.lastname.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route('/property/create', methods=['GET', 'POST'])
@admin_required
def add_property():
    form = AddPropertyForm()

    if form.validate_on_submit():
        flash('Group bigga successfully!', 'success')
        # Collect form data
        name = form.name.data
        location = form.location.data
        description = form.description.data
        bedrooms = form.bedrooms.data
        bathrooms = form.bathrooms.data
        beds = form.beds.data
        guests = form.guests.data
        size = form.size.data
        price = form.price.data
        latitude = form.latitude.data
        longitude = form.longitude.data

        # Create a new Property instance
        new_property = Property(
            name=name,
            location=location,
            description=description,
            bedroom_count=bedrooms,
            bathroom_count=bathrooms,
            bed_count=beds,
            guest_capacity=guests,
            size_sqft=size,
            price_per_night=price,
            latitude=latitude,
            longitude=longitude
        )

        # Commit the new property to the database
        db.session.add(new_property)
        db.session.commit()
        flash('Group created successfully!', 'success')
        return redirect(url_for('index'))  # Redirect to property listing page after adding
    
    else:
        print(form.errors)

    return render_template('add_property.html', form=form)


@app.route('/property/<int:property_id>/manage', methods=['GET','POST'])
@admin_required
def manage_property(property_id):
    property = Property.query.get_or_404(property_id)
    if request.method == 'POST':
        if 'save_location' in request.form:
            new_location = request.form.get('location')
            property.location = new_location
            db.session.commit()
            flash('Property location updated succesfully.', 'success')
            return redirect(url_for('manage_property', property_id=property_id))
        elif 'save_name' in request.form:
            # Save the updated group description
            new_name = request.form.get('name')
            property.name = new_name
            db.session.commit()
            flash('Property name updated successfully.', 'success')
            return redirect(url_for('manage_property', property_id=property_id))
        elif 'save_bedroom_count' in request.form:
            new_bedroom_count = request.form.get('bedroom_count')
            property.bedroom_count = new_bedroom_count
            db.session.commit()
            flash('Property bedroom_count updated succesfully.', 'success')
            return redirect(url_for('manage_property', property_id=property_id))
        elif 'save_bathroom_count' in request.form:
            new_bathroom_count = request.form.get('bathroom_count')
            property.bathroom_count = new_bathroom_count
            db.session.commit()
            flash('Property bathroom_count updated succesfully.', 'success')
            return redirect(url_for('manage_property', property_id=property_id))
        elif 'save_bed_count' in request.form:
            new_bed_count = request.form.get('bed_count')
            property.bed_count = new_bed_count
            db.session.commit()
            flash('Property bed_count updated succesfully.', 'success')
            return redirect(url_for('manage_property', property_id=property_id))
        elif 'save_size_sqft' in request.form:
            new_size_sqft = request.form.get('size_sqft')
            property.size_sqft = new_size_sqft
            db.session.commit()
            flash('Property size_sqft updated succesfully.', 'success')
            return redirect(url_for('manage_property', property_id=property_id))
        elif 'save_description' in request.form:
            new_description = request.form.get('description')
            property.description = new_description
            db.session.commit()
            flash('Property location updated succesfully.', 'success')
            return redirect(url_for('manage_property', property_id=property_id))
        elif 'save_latitudelongitude' in request.form:
            new_latitude = request.form.get('latitude')
            new_longitude = request.form.get('longitude')
            property.latitude = new_latitude
            property.longitude = new_longitude
            db.session.commit()
            flash('Property latitudelongitude updated succesfully.', 'success')
            return redirect(url_for('manage_property', property_id=property_id))
        
    return render_template('property_manage.html', property=property)

@app.route('/property/<int:property_id>/', methods=['GET', 'POST'])
def property_detail(property_id):
    user = None
    if current_user.is_authenticated:
        user = db.first_or_404(sa.select(User).where(User.email == current_user.email))
    property = Property.query.get_or_404(property_id)
    return render_template('property.html', user=user,property=property)

@app.route('/property/<int:property_id>/add_amenities', methods=['GET', 'POST'])
def add_amenities_to_property(property_id):
    property_instance = Property.query.get_or_404(property_id)
    amenities = Amenity.query.all()  # Fetch all available amenities
    form = AddAmenitiesToPropertyForm(property_instance=property_instance)

    if form.validate_on_submit():
        # Add selected amenities to the property
        property_instance.amenities.extend(form.amenities.data)
        
        db.session.commit()
        flash("Amenities added successfully!", "success")
        return redirect(url_for('controlpanel', property_id=property_instance.id))  # Redirect to property details page

    return render_template('add_amenities.html', form=form, property_instance=property_instance, amenities=amenities)

@app.route('/controlpanel', methods=['GET', 'POST'])
@login_required
@admin_required
def controlpanel():
    users = User.query.all()  # Fetch all users for the admin to manage
    form = AddAmenityForm()
    if form.validate_on_submit():
        new_amenity = Amenity(name=form.name.data, icon=form.icon.data)
        db.session.add(new_amenity)
        db.session.commit()
        flash("Amenity added successfully!", "success")
        return redirect(url_for('manage_amenities'))  # Stay on the amenities page
    amenities = Amenity.query.all()

    if request.method == 'POST':
        user_id = request.form.get('user_id')  # Get selected user ID
        user = User.query.get(user_id)
        if user:
            user.role = 'administrator'
            db.session.commit()
            flash(f"{user.firstname} {user.lastname} is now an administrator!", "success")
        else:
            flash("User not found.", "danger")

    return render_template('controlpanel.html', users=users, form=form, amenities=amenities)
    