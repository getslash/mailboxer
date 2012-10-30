import flask
from . import config
from . import db

def authenticate_from_openid_response(resp):
    flask.session["user"] = dict(
        openid = resp.identity_url,
        email = resp.email,
        )

def deauthenticate():
    flask.session.pop("user", None)

def get_user_email():
    return _get_user_attribute("email")

def _get_user_attribute(attr):
    auth_info = flask.session.get("user")
    if auth_info is None:
        return None
    return auth_info.get(attr, None)

def is_authenticated():
    if not config.app.REQUIRE_LOGIN:
        return True
    return "user" in flask.session
