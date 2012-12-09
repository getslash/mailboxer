import os
import sys
import logging
from logging.handlers import WatchedFileHandler
from deployment import fix_paths
from config import config
import flask
from flask.ext.openid import OpenID
from flask.ext.gravatar import Gravatar
from . import auth
from . import db
from .utils import render_template

app = flask.Flask(__name__, static_folder=os.path.join(fix_paths.PROJECT_ROOT, "www", "static"))
app.config["SECRET_KEY"] = config.flask.secret_key

db.db.init_app(app)

@app.before_first_request
def _check_secret_key():
    if not app.config["SECRET_KEY"]:
        raise RuntimeError("No secret key configured!")

db.db.init_app(app)

gravatar = Gravatar(app,
                    size=24,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False)

oid = OpenID(app, config.deployment.openid.storage_path)

@app.before_first_request
def _setup_logging():
    if not app.debug:
        file_handler = WatchedFileHandler(config.deployment.log_path)
        file_handler.setLevel(logging.WARNING)
        app.logger.addHandler(file_handler)

@app.route("/")
def index():
    return render_template("index.html")

@app.route('/login')
@oid.loginhandler
def login():
    """
    Does the login via OpenID.  Has to call into `oid.try_login`
    to start the OpenID machinery.
    """
    # if we are already logged in, go back to were we came from
    if auth.is_authenticated():
        return flask.redirect(oid.get_next_url())
    return oid.try_login("https://www.google.com/accounts/o8/id", 
                         ask_for=['email', 'fullname', 'nickname'])

@app.route("/logout")
def logout():
    if auth.is_authenticated():
        auth.deauthenticate()
    return flask.redirect(oid.get_next_url())

@oid.after_login
def create_or_login(resp):
    auth.authenticate_from_openid_response(resp)
    return flask.redirect(oid.get_next_url())
