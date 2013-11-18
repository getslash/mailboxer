from .app import app
from flask.ext.sqlalchemy import SQLAlchemy

db = SQLAlchemy(app)

_EMAIL_TYPE = db.String(160)

emails_to_mailboxes = db.Table('emails_to_mailboxes',
    db.Column('mailbox_id', db.Integer, db.ForeignKey('mailbox.id')),
    db.Column('email_id', db.Integer, db.ForeignKey('email.id'))
)

class Mailbox(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(_EMAIL_TYPE, unique=True)

class Email(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    recipients = db.relationship(Mailbox, secondary=emails_to_mailboxes, backref=db.backref('emails', lazy='dynamic'))
    fromaddr = db.Column(_EMAIL_TYPE)
    message = db.Column(db.Text())
    sent_via_ssl = db.Column(db.Boolean)

