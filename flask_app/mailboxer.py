from httplib import (
    BAD_REQUEST,
)
from flask import abort
from flask import Blueprint
from flask import request
import logging

from .db import (
    get_mailbox_collection,
    get_message_collection,
    )
from . import messages
from .utils import returns_json
from .utils import render_template

blueprint = Blueprint("mail", __name__)

@blueprint.route("/mailboxes/")
@returns_json
def get_all_mailboxes():
    return [{"name" : m["name"]} for m in get_mailbox_collection().find()]

@blueprint.route("/mailboxes/", methods=["POST"])
@returns_json
def add_mailbox():
    data = _check_request_data("name")
    if "*" in data["name"]:
        abort(BAD_REQUEST)
    get_mailbox_collection().save(data)
    assert isinstance(data["name"], basestring)
    return dict(name=data["name"])

@blueprint.route("/mailboxes/<mailbox_name>", methods=["DELETE"])
@returns_json
def delete_mailbox(mailbox_name):
    get_mailbox_collection().remove({"name":mailbox_name})
    messages.delete_messages_by_mailbox(mailbox_name)
    return {}

@blueprint.route("/mailboxes/*", methods=["DELETE"])
@returns_json
def delete_all_mailboxes():
    get_mailbox_collection().remove()
    messages.delete_all_messages()
    return {}

@blueprint.route("/messages/<mailbox_name>")
@returns_json
def get_messages(mailbox_name):
    return messages.get_messages(mailbox_name)

@blueprint.route("/messages/<mailbox_name>/unread")
@returns_json
def get_unread_messages(mailbox_name):
    return messages.get_messages(mailbox_name, include_read=False)


@blueprint.route("/summary")
def get_summary_page():
    summary = {}
    mailboxes = summary["mailboxes"] = []
    for mailbox in get_mailbox_collection().find():
        mailbox = {"name" : mailbox["name"],
                   "num_messages" : get_message_collection().find({"mailbox_name" : mailbox["name"]}).count()}
        mailboxes.append(mailbox)
    return render_template("index.html", summary=summary)

def _check_request_data(*fields):
    data = request.json
    if data is None and request.form is not None:
        data = {k : v for k, v in request.form.iteritems()}
    if data is None or set(data) != set(fields):
        abort(400)
    logging.debug("Request data: %s", data)
    return dict(data)
