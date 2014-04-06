import httplib

from flask import abort, Blueprint, jsonify, request

from weber_utils import (dictify_model, paginate_query, paginated_view,
                         takes_schema_args)

from .models import *

blueprint = Blueprint("v2", __name__)

@blueprint.route("/mailboxes", methods=["post"])
@takes_schema_args(address=str)
def create_mailbox(address):
    mailbox = Mailbox(address=address)
    db.session.add(mailbox)
    db.session.commit()
    return jsonify(dictify_model(mailbox))


@blueprint.route("/mailboxes")
@paginated_view
def list_mailboxes():
    return Mailbox.query

@blueprint.route("/mailboxes/<address>/emails")
@paginated_view
def list_all_mailbox_emails(address):
    return Email.query.join(Mailbox).filter(Mailbox.address==address).order_by(Email.timestamp)

@blueprint.route("/mailboxes/<address>/unread_emails")
def list_unread_mailbox_emails(address):
    query = Email.query.join(Mailbox).filter(Mailbox.address==address, Email.read==False).order_by(Email.timestamp)
    returned = paginate_query(query)
    if returned["result"]:
        Email.query.filter(Email.id.in_([obj["id"] for obj in returned["result"]])).update({Email.read: True}, synchronize_session="fetch")
    db.session.commit()
    return jsonify(returned)

@blueprint.route("/vacuum", methods=["post"])
def vacuum_old_mailboxes():
    max_age_seconds = request.args.get("max_age_seconds")
    try:
        max_age_seconds = int(max_age_seconds)
    except (ValueError, TypeError):
        abort(httplib.BAD_REQUEST)

    threshold = datetime.datetime.utcnow() - datetime.timedelta(seconds=max_age_seconds)

    Mailbox.query.filter(Mailbox.last_activity < threshold).delete()
    db.session.commit()
    return "ok"
