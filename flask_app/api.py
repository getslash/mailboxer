from flask import Blueprint, jsonify

from .models import *
from .pagination import paginated_view, paginate_query
from weber_utils import dictify_model, takes_schema_args

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
    return Email.query.join(Mailbox).filter(Mailbox.address==address)

@blueprint.route("/mailboxes/<address>/unread_emails")
def list_unread_mailbox_emails(address):
    query = Email.query.join(Mailbox).filter(Mailbox.address==address, Email.read==False).order_by(Email.timestamp)
    returned = paginate_query(query)
    if returned["result"]:
        Email.query.filter(Email.id.in_([obj["id"] for obj in returned["result"]])).update({Email.read: True}, synchronize_session="fetch")
    db.session.commit()
    return jsonify(returned)
