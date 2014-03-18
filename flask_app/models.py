import datetime

from flask.ext.sqlalchemy import SQLAlchemy

from .app import app

db = SQLAlchemy(app)

_EMAIL_TYPE = db.String(160)

class Mailbox(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    address = db.Column(_EMAIL_TYPE, unique=True, index=True)
    last_activity = db.Column(db.DateTime, default=datetime.datetime.utcnow, index=True)

class Email(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mailbox_id = db.Column(db.Integer, db.ForeignKey("mailbox.id"), index=True)
    mailbox = db.relationship("Mailbox", backref="emails")
    fromaddr = db.Column(_EMAIL_TYPE)
    message = db.Column(db.Text())
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow, index=True)
    sent_via_ssl = db.Column(db.Boolean)
    read = db.Column(db.Boolean, default=False)
