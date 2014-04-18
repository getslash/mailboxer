import datetime
import itertools
import os
import shutil
import subprocess
import sys
import tempfile
import uuid

import requests
from flask.ext.loopback import FlaskLoopback
from urlobject import URLObject as URL

import pytest
from flask_app import app, models
from mailboxer import Mailboxer

from .test_utils import send_mail

#import from mailboxer-python

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

def pytest_addoption(parser):
    parser.addoption("--www-port", action="store", default=8000, type=int)
    parser.addoption("--no-setup-db", action="store_true", default=False)

@pytest.fixture
def deployment_webapp_url(request):
    port = request.config.getoption("--www-port")
    return URL("http://127.0.0.1").with_port(port)

@pytest.fixture(autouse=True, scope="session")
def db_engine(request):
    if request.config.getoption("--no-setup-db"):
        return
    tmpdir = tempfile.mkdtemp()
    subprocess.check_call("pg_ctl init -D {0} -w".format(tmpdir), shell=True)
    subprocess.check_call("pg_ctl start -D {0} -w".format(tmpdir), shell=True)
    @request.addfinalizer
    def finalize():
        subprocess.check_call("pg_ctl stop -D {0} -w -m immediate".format(tmpdir), shell=True)
        shutil.rmtree(tmpdir)

    subprocess.check_call("createdb mailboxer", shell=True)

@pytest.fixture
def webapp(request, db):
    returned = Webapp(app.app)
    returned.app.config["SECRET_KEY"] = "testing_key"
    returned.app.config["TESTING"] = True
    returned.activate()
    request.addfinalizer(returned.deactivate)
    return returned

@pytest.fixture(autouse=True, scope="function")
def db(request):
    models.db.session.close()
    models.db.drop_all()
    models.db.create_all()

@pytest.fixture
def mailboxer(webapp):
    return Mailboxer("http://{0}".format(webapp.hostname))


class Webapp(object):

    def __init__(self, app):
        super(Webapp, self).__init__()
        self.app = app
        self.loopback = FlaskLoopback(self.app)
        self.hostname = str(uuid.uuid1())

    def activate(self):
        self.loopback.activate_address((self.hostname, 80))

    def deactivate(self):
        self.loopback.deactivate_address((self.hostname, 80))

    def _request(self, method, path, *args, **kwargs):
        raw_response = kwargs.pop("raw_response", False)
        if path.startswith("/"):
            path = path[1:]
            assert not path.startswith("/")
        returned = requests.request(method, "http://{0}/{1}".format(self.hostname, path), *args, **kwargs)
        if raw_response:
            return returned

        returned.raise_for_status()
        return returned.json()

    def get_single_page(self, path):
        returned = self.get(path)
        assert returned['metadata']['total_num_pages'] == 1
        assert returned['metadata']['page'] == 1
        return returned["result"]


def _make_request_shortcut(method_name):
    def json_method(self, *args, **kwargs):
        return self._request(method_name, *args, **kwargs)

    json_method.__name__ = method_name
    setattr(Webapp, method_name, json_method)

    def raw_method(self, *args, **kwargs):
        return self._request(method_name, raw_response=True, *args, **kwargs)

    raw_method.__name__ = "{0}_raw".format(method_name)
    setattr(Webapp, raw_method.__name__, raw_method)

for _method in ("get", "put", "post", "delete"):
    _make_request_shortcut(_method)


################################################################################
_id_generator = itertools.count()

@pytest.fixture
def page_size(request):
    return 100

@pytest.fixture
def recipient(mailboxer):
    return make_recipient(mailboxer)

@pytest.fixture
def recipients(mailboxer):
    return [make_recipient(mailboxer) for i in range(5)]

def make_recipient(mailboxer):
    recipient = Recipient()
    mailboxer.create_mailbox(recipient.address)
    return recipient

@pytest.fixture
def inactive_recipient(mailboxer):
    returned = recipient(mailboxer)
    mailbox = returned.get_mailbox_obj()
    mailbox.last_activity -= datetime.timedelta(seconds=1000)
    models.db.session.add(mailbox)
    models.db.session.commit()
    return returned

class Recipient(object):

    def __init__(self):
        super(Recipient, self).__init__()
        self.address = "recipient{}@some.domain.com".format(next(_id_generator))

    def get_mailbox_obj(self):
        return models.Mailbox.query.filter(models.Mailbox.address == self.address).one()

@pytest.fixture
def unsent_email():
    return Email()

@pytest.fixture
def email(recipient):
    returned = Email()
    send_mail(returned.fromaddr, [recipient.address], returned.message)
    return returned

@pytest.fixture
def emails(recipient, num_emails=5):
    returned = [Email() for i in range(5)]
    for e in returned:
        send_mail(e.fromaddr, [recipient.address], e.message)
    return returned

class Email(object):

    def __init__(self):
        super(Email, self).__init__()
        self.fromaddr = "from{}@some.domain.com".format(next(_id_generator))
        self.message = "message here!"


################################################################################
