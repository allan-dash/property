from flask import render_template, flash, redirect, url_for, request, Flask, jsonify
import logging
from app import app, db
from app.forms import LoginForm, RegistrationForm, EditProfileForm, EmptyForm, PostForm, ResetPasswordRequestForm, ResetPasswordForm, CreateGroupForm, AddUserToGroupForm
from flask_login import current_user, login_user, logout_user, login_required
import sqlalchemy as sa
from app.models import User, Post, Group, GroupMembership, Message
from urllib.parse import urlsplit
from datetime import datetime, timezone
from app.email import send_password_reset_email
from sqlalchemy import func
from werkzeug.utils import secure_filename
from sqlalchemy.orm import joinedload
import os
from flask import send_from_directory
from PIL import Image
import random
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}



logging.basicConfig(filename='flask_debug.log', level=logging.DEBUG)

@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def index():
    return render_template('index.html', title='Home')

@app.route('/property', methods=['GET', 'POST'])
def property():
    return render_template('property.html', title='Home')