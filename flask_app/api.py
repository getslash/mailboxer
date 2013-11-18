from flask import Blueprint, jsonify

from . import models
from .pagination import paged_view
from .request_utils import dictify_model, takes_schema_args

blueprint = Blueprint("v2", __name__)

@blueprint.route("/mailboxes", methods=["post"])
@takes_schema_args(email=str)
def create_mailbox(email):
    mailbox = models.Mailbox(email=email)
    models.db.session.add(mailbox)
    models.db.session.commit()
    return jsonify(dictify_model(mailbox))


@blueprint.route("/mailboxes")
@paged_view
def list_mailboxes():
    return models.Mailbox.query
