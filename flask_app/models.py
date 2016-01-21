import datetime

from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.security import UserMixin, RoleMixin

from sqlalchemy.orm import backref


db = SQLAlchemy()

_EMAIL_TYPE = db.String(160)

class Mailbox(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    address = db.Column(_EMAIL_TYPE, unique=True, index=True)
    last_activity = db.Column(db.DateTime, default=datetime.datetime.utcnow, index=True)
    emails = db.relationship("Email", backref=backref("mailbox"), cascade="all, delete, delete-orphan")

class Email(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mailbox_id = db.Column(db.Integer, db.ForeignKey("mailbox.id", ondelete="CASCADE"), index=True)
    #mailbox = db.relationship("Mailbox", backref=backref("emails"), cascade="all, delete, delete-orphan", single_parent=True)
    fromaddr = db.Column(_EMAIL_TYPE)
    message = db.Column(db.Text())
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow, index=True)
    sent_via_ssl = db.Column(db.Boolean)
    read = db.Column(db.Boolean, default=False)

roles_users = db.Table('roles_users',
                       db.Column('user_id', db.Integer(), db.ForeignKey('user.id', ondelete='CASCADE')),
                       db.Column('role_id', db.Integer(), db.ForeignKey('role.id', ondelete='CASCADE')))


class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
    active = db.Column(db.Boolean())
    confirmed_at = db.Column(db.DateTime())
    roles = db.relationship('Role', secondary=roles_users,
                            backref=db.backref('users', lazy='dynamic'))
