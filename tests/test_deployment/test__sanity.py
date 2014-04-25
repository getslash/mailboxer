from smtplib import SMTP
from uuid import uuid1

import requests

from mailboxer import Mailboxer


def test_get_index_page(deployment_webapp_url):
    requests.get(deployment_webapp_url).raise_for_status()

def test_send_receive_email(deployment_webapp_url, deployment_smtp_port):
    m = Mailboxer(deployment_webapp_url)
    address = "{0}@example.com".format(uuid1())
    mailbox = m.create_mailbox(address)
    try:
        s = SMTP("127.0.0.1", deployment_smtp_port)
        mailbox = m.get_mailbox(address)
        assert len(mailbox.get_emails()) == 0
        s.sendmail("from@something.com", [address], "message")
        assert len(mailbox.get_emails()) == 1
    finally:
        mailbox.delete()
