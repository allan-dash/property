from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, current_user
import logging
from logging.handlers import RotatingFileHandler, SMTPHandler
import os
from flask_mail import Mail
from flask_socketio import SocketIO, emit
from flask import request



app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
socketio = SocketIO(app)
migrate = Migrate(app, db)
login = LoginManager(app)
login.login_view = 'login'
mail = Mail(app)
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_recycle' : 280}
app.config['UPLOAD_FOLDER'] = '/uploads/icons'
app.config['MAX_CONTENT_LENGTH'] = 4 * 1024 * 1024  # 16MB max file size

app.logger.setLevel(logging.DEBUG)
logging.basicConfig(filename='flask_debug.log', level=logging.DEBUG)


if not app.debug:
    if app.config['MAIL_SERVER']:
        auth = None
        if app.config['MAIL_USERNAME'] or app.config['MAIL_PASSWORD']:
            auth = (app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
        secure = None
        if app.config['MAIL_USE_TLS']:
            secure = ()
        mail_handler = SMTPHandler(
            mailhost=(app.config['MAIL_SERVER'], app.config['MAIL_PORT']),
            fromaddr='no-reply@' + app.config['MAIL_SERVER'],
            toaddrs=app.config['ADMINS'], subject='Microblog Failure',
            credentials=auth, secure=secure)
        mail_handler.setLevel(logging.ERROR)
        app.logger.addHandler(mail_handler)

    if not os.path.exists('logs'):
        os.mkdir('logs')
    file_handler = RotatingFileHandler('logs/microblog.log', maxBytes=10240,
                                       backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)

    app.logger.setLevel(logging.INFO)
    app.logger.info('Microblog startup')


@socketio.on('connect')
def handle_connect():
    if current_user.is_authenticated:
        current_user.socket_id = request.sid  # Assign session ID to the user
        db.session.commit()
        app.logger.debug(f"User {current_user.username} connected with socket ID {request.sid}")
    else:
        app.logger.debug("Anonymous user connected")



@socketio.on('disconnect')
def handle_disconnect():
    if current_user.is_authenticated:
        current_user.socket_id = None  # Clean up when the user disconnects
        db.session.commit()
        app.logger.debug(f"User {current_user.id} disconnected, socket ID removed.")


@socketio.on('send_message')
def handle_send_message(data):
    from app.models import User, Message
    sender_id = current_user.id
    recipient_id = data['recipient_id']
    content = data['content']

    # Ensure that the recipient exists
    recipient = User.query.get(recipient_id)
    if recipient:
        # Save the message to the database
        message = Message(sender_id=sender_id, recipient_id=recipient_id, content=content)
        db.session.add(message)
        db.session.commit()

        # Emit the message to the recipient
        emit('new_message', {
            'sender': current_user.username,
            'content': content,
            'recipient_id': recipient_id
        }, room=recipient.socket_id)

        # Emit the message to the sender without relying on the broadcast
        emit('new_message', {
            'sender': current_user.username,
            'content': content,
            'recipient_id': recipient_id
        }, room=request.sid)  # Send only to the sender
    else:
        app.logger.error(f"Recipient {recipient_id} not found")


from app import routes, models, errors

