import flask
from flaskext.openid import OpenID
from .logs import blueprint
from . import config
from . import auth
from .utils import render_template

app = flask.Flask(__name__)
app.config.update(config.__dict__)
oid = OpenID(app)

@app.route("/")
def index():
    if not auth.is_authenticated():
        return flask.redirect("/login")
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

@oid.after_login
def create_or_login(resp):
    auth.authenticate_from_openid_response(resp)
    return flask.redirect(oid.get_next_url())
