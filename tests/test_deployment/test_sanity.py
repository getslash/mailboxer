import time
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
        [email] = _wait_for_emails(mailbox)
    finally:
        mailbox.delete()

def _wait_for_emails(mailbox, num_retries=5, sleep_time_seconds=0.5):
    for retry in range(num_retries):
        if retry > 0:
            time.sleep(sleep_time_seconds)
        emails = list(mailbox.get_emails())
        if emails:
            return emails
    assert False, "Emails did not arrive"
