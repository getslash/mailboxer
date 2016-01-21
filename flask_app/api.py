import calendar
import datetime
import requests

from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import IntegrityError

from flask import abort, Blueprint, jsonify, current_app

from weber_utils import (dictify_model, paginate_query, paginated_view, sorted_view,
                         takes_schema_args)

from .models import Email, Mailbox, db

blueprint = Blueprint("v2", __name__)


@blueprint.route("/mailboxes", methods=["post"])
@takes_schema_args(address=str)
def create_mailbox(address):
    mailbox = Mailbox(address=address)
    db.session.add(mailbox)
    try:
        db.session.commit()
    except IntegrityError:
        abort(requests.codes.conflict)  # pylint: disable=no-member
    return jsonify(dictify_model(mailbox))


def _render_mailbox(mailbox):
    timestamp = calendar.timegm(mailbox.last_activity.utctimetuple())
    return {
        "address": mailbox.address,
        "last_activity": timestamp,
        "will_delete": timestamp + current_app.config["MAX_MAILBOX_AGE_SECONDS"],
    }


@blueprint.route("/mailboxes")
@paginated_view(renderer=_render_mailbox)
@sorted_view(allowed_fields=["last_activity", "id"])
def list_mailboxes():
    return Mailbox.query  # pylint: disable=no-member


@blueprint.route("/mailboxes/<address>", methods=["delete"])
def delete_mailbox(address):
    Mailbox.query.filter(Mailbox.address == address).delete(
    )  # pylint: disable=no-member
    db.session.commit()
    return jsonify(_SUCCESS)


@blueprint.route("/mailboxes/<address>/emails")
@paginated_view
def list_all_mailbox_emails(address):
    _check_mailbox_exists(address)
    return Email.query.join(Mailbox).filter(Mailbox.address == address).order_by(Email.timestamp)  # pylint: disable=no-member


@blueprint.route("/mailboxes/<address>/unread_emails")
def list_unread_mailbox_emails(address):
    _check_mailbox_exists(address)
    query = Email.query.join(Mailbox).filter(Mailbox.address == address, Email.read == False).order_by(Email.timestamp)  # pylint: disable=no-member,singleton-comparison
    returned = paginate_query(query)
    if returned["result"]:
        Email.query.filter(Email.id.in_([obj["id"] for obj in returned["result"]])).update({Email.read: True}, synchronize_session="fetch")  # pylint: disable=no-member
    db.session.commit()
    return jsonify(returned)


def _check_mailbox_exists(address):
    try:
        _ = Mailbox.query.filter(Mailbox.address == address).one()  # pylint: disable=no-member
    except NoResultFound:
        abort(requests.codes.not_found)  # pylint: disable=no-member


@blueprint.route("/vacuum", methods=["post"])
def vacuum_old_mailboxes():
    max_age_seconds = current_app.config["MAX_MAILBOX_AGE_SECONDS"]

    threshold = datetime.datetime.utcnow() - datetime.timedelta(seconds=max_age_seconds)

    Mailbox.query.filter(Mailbox.last_activity < threshold).delete()  # pylint: disable=no-member
    db.session.commit()
    return jsonify(_SUCCESS)

_SUCCESS = {"result": "success"}
