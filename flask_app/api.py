from flask import Blueprint

from .request_utils import takes_schema_args

blueprint = Blueprint("v2", __name__)

@blueprint.route("/mailboxes", methods=["post"])
@takes_schema_args(name=str)
def create_mailbox(name):
    return "OK!"
