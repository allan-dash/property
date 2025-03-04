from flask_mail import Message
from flask import render_template
from app import mail
from mailjet_rest import Client
import os

def send_email(subject, sender, recipients, text_body, html_body):
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    mail.send(msg)

    
def send_password_reset_email(user):
    token = user.get_reset_password_token()
    api_key = 'c282ac1ce1a4940dbef4fff1405bb748'
    api_secret = '9ccde72cee5e6eb61405a0cfd4a25656'
    mailjet = Client(auth=(api_key, api_secret))
    data = {
    'FromEmail': 'no-reply@findroleplay.com',
    'FromName': 'findroleplay',
    'Subject': 'Password Reset Confirmation',
    'Text-part': render_template('email/reset_password.txt', user=user, token=token),
    'Html-part': render_template('email/reset_password.html', user=user, token=token),
    'Recipients': [{'Email':user.email}]
    }
    result = mailjet.send.create(data=data)
    print(result.text)  # Check the raw response body
    try:
        print(result.json())  # Only try parsing as JSON if valid
    except ValueError:
        print("Response is not in JSON format")