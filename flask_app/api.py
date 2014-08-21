import calendar
import requests

from sqlalchemy.orm.exc import NoResultFound

from flask import abort, Blueprint, jsonify, request

from weber_utils import (dictify_model, paginate_query, paginated_view, sorted_view,
                         takes_schema_args)

from .app import app
from .models import *

blueprint = Blueprint("v2", __name__)

@blueprint.route("/mailboxes", methods=["post"])
@takes_schema_args(address=str)
def create_mailbox(address):
    mailbox = Mailbox(address=address)
    db.session.add(mailbox)
    db.session.commit()
    return jsonify(dictify_model(mailbox))

def _render_mailbox(mailbox):
    timestamp = calendar.timegm(mailbox.last_activity.utctimetuple())
    return {
        "address": mailbox.address,
        "last_activity": timestamp,
        "will_delete": timestamp + app.config["MAX_MAILBOX_AGE_SECONDS"],
    }

@blueprint.route("/mailboxes")
@paginated_view(renderer=_render_mailbox)
@sorted_view(allowed_fields=["last_activity", "id"])
def list_mailboxes():
    return Mailbox.query

@blueprint.route("/mailboxes/<address>", methods=["delete"])
def delete_mailbox(address):
    Mailbox.query.filter(Mailbox.address==address).delete()
    db.session.commit()
    return jsonify(_SUCCESS)

@blueprint.route("/mailboxes/<address>/emails")
@paginated_view
def list_all_mailbox_emails(address):
    _check_mailbox_exists(address)
    return Email.query.join(Mailbox).filter(Mailbox.address==address).order_by(Email.timestamp)

@blueprint.route("/mailboxes/<address>/unread_emails")
def list_unread_mailbox_emails(address):
    _check_mailbox_exists(address)
    query = Email.query.join(Mailbox).filter(Mailbox.address==address, Email.read==False).order_by(Email.timestamp)
    returned = paginate_query(query)
    if returned["result"]:
        Email.query.filter(Email.id.in_([obj["id"] for obj in returned["result"]])).update({Email.read: True}, synchronize_session="fetch")
    db.session.commit()
    return jsonify(returned)

def _check_mailbox_exists(address):
    try:
        Mailbox.query.filter(Mailbox.address==address).one()
    except NoResultFound:
        abort(requests.codes.not_found)

@blueprint.route("/vacuum", methods=["post"])
def vacuum_old_mailboxes():
    max_age_seconds = app.config["MAX_MAILBOX_AGE_SECONDS"]

    threshold = datetime.datetime.utcnow() - datetime.timedelta(seconds=max_age_seconds)

    Mailbox.query.filter(Mailbox.last_activity < threshold).delete()
    db.session.commit()
    return jsonify(_SUCCESS)

_SUCCESS = {"result": "success"}
