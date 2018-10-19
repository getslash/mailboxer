import datetime
import itertools
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import uuid

import requests
import yarl
import pytest
from mailboxer import Mailboxer

from .test_utils import send_mail

# import from mailboxer-python

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))



@pytest.fixture(scope="session", autouse=True)
def mailboxer_process(smtp_port, webapp_port):
    if os.environ.get('MAILBOXER_SPAWN_SERVER', 'true').lower() == 'true':
        process = subprocess.Popen("cargo run", shell=True)
        print("Started process", process.pid)
    else:
        process = None
    check_connectivity(smtp_port, process)
    check_connectivity(webapp_port, process)

    try:
        yield process
    finally:
        if process is not None:
            process.terminate()
            process.wait()
    return process


def check_connectivity(port, process, *, timeout=60):
    end_time = time.time() + timeout
    while process is None or  process.poll() is None:
        try:
            if port == 80:
                requests.get(f"http://127.0.0.1:{port}")
            else:
                s = socket.socket()
                s.connect(("127.0.0.1", port))
        except socket.error:
            if time.time() > end_time:
                raise
            time.sleep(0.1)
        else:
            break
    if process is not None and process.poll() is not None:
        raise RuntimeError("Process terminated!")
    print('*** Port', port, 'is responsive')



@pytest.fixture(scope="session")
def webapp_url(request, webapp_port):
    return yarl.URL.build(scheme="http", host="127.0.0.1", port=webapp_port)

@pytest.fixture(scope="session")
def webapp_port():
    return int(os.environ.get('MAILBOXER_HTTP_PORT', 8000))

@pytest.fixture(scope="session")
def smtp_port(request):
    return int(os.environ.get('MAILBOXER_SMTP_PORT', 2525))


@pytest.fixture
def webapp(request, webapp_url):
    returned = Webapp(webapp_url)
    return returned


@pytest.fixture
def mailboxer(webapp):
    return Mailboxer(webapp.url)


class Webapp:

    def __init__(self, url):
        super().__init__()
        self.url = url

    def _request(self, method, path, *args, **kwargs):
        raw_response = kwargs.pop("raw_response", False)
        returned = requests.request(method, self.url / path, *args, **kwargs)
        if raw_response:
            return returned

        returned.raise_for_status()
        return returned.json()

    def get_single_page(self, path):
        returned = self.get(path)
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


##########################################################################
_id_generator = itertools.count()


@pytest.fixture
def page_size(request):
    return 100


@pytest.fixture
def recipient(request, mailboxer):
    return make_recipient(request, mailboxer)


@pytest.fixture
def recipients(request, mailboxer):
    return [make_recipient(request, mailboxer) for i in range(5)]


def make_recipient(request, mailboxer):
    recipient = Recipient()
    mailbox = mailboxer.create_mailbox(recipient.address)
    request.addfinalizer(mailbox.delete)
    return recipient


class Recipient(object):

    def __init__(self):
        super(Recipient, self).__init__()
        self.address = "recipient{}@some.domain.com".format(
            next(_id_generator))


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


##########################################################################
