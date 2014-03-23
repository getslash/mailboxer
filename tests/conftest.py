import itertools
import datetime
import os
import sys
import uuid

import requests
from flask.ext.loopback import FlaskLoopback
from urlobject import URLObject as URL

import pytest
from flask_app import app, models

from .test_utils import send_mail

#import from mailboxer-python
from mailboxer import Mailboxer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

def pytest_addoption(parser):
    parser.addoption("--www-port", action="store", default=8080, type=int)

@pytest.fixture
def deployment_webapp_url(request):
    port = request.config.getoption("--www-port")
    return URL("http://127.0.0.1").with_port(port)

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
        if path.startswith("/"):
            path = path[1:]
            assert not path.startswith("/")
        return requests.request(method, "http://{0}/{1}".format(self.hostname, path), *args, **kwargs)

    def get(self, *args, **kwargs):
        return self._request("get", *args, **kwargs)

    def post(self, *args, **kwargs):
        return self._request("post", *args, **kwargs)

    def delete(self, *args, **kwargs):
        return self._request("delete", *args, **kwargs)

    def put(self, *args, **kwargs):
        return self._request("put", *args, **kwargs)

    def get_single_page(self, path):
        returned = self.get(path).json()
        assert returned['metadata']['total_num_pages'] == 1
        assert returned['metadata']['page'] == 1
        return returned["result"]

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
