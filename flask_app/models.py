import datetime

from flask.ext.sqlalchemy import SQLAlchemy

from sqlalchemy.orm import backref

from .app import app

db = SQLAlchemy(app)

_EMAIL_TYPE = db.String(160)

class Mailbox(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    address = db.Column(_EMAIL_TYPE, unique=True, index=True)
    last_activity = db.Column(db.DateTime, default=datetime.datetime.utcnow, index=True)
    emails = db.relationship("Email", backref="mailbox", cascade="all, delete, delete-orphan")

class Email(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mailbox_id = db.Column(db.Integer, db.ForeignKey("mailbox.id"), index=True)
    # mailbox = db.relationship("Mailbox", backref=backref("emails", cascade="all,delete"))
    fromaddr = db.Column(_EMAIL_TYPE)
    message = db.Column(db.Text())
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow, index=True)
    sent_via_ssl = db.Column(db.Boolean)
    read = db.Column(db.Boolean, default=False)
