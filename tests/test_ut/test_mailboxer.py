import datetime
import logging

from flask_app import models

from ..test_utils import send_mail


def test_get_mailboxes(webapp, recipient):
    [mailbox] = webapp.get_single_page("/v2/mailboxes")
    assert mailbox["address"] == recipient.address

def test_incoming_message_no_mailbox_match():
    send_mail("fromaddr@somedomain.com", ["blap@bloop.com"], "message")
    assert models.Email.query.count() == 0


def test_get_all_emails(webapp, recipient, emails):
    received = webapp.get_single_page("/v2/mailboxes/{}/emails".format(recipient.address))
    assert len(received) == len(emails)
    for r, e in zip(received, emails):
        assert r["fromaddr"] == e.fromaddr

def test_get_mailboxes_pagination(webapp, recipients, page_size):
    result = webapp.get("/v2/mailboxes?page_size={0}".format(page_size)).json()
    assert result["metadata"]["total_num_pages"] == 1
    assert result["metadata"]["total_num_objects"] == len(recipients)

def test_send_receive_email(webapp, recipient, email):
    received_emails = webapp.get_single_page("/v2/mailboxes/{}/emails".format(recipient.address))
    assert len(received_emails) == 1
    [received] = received_emails
    received.pop("timestamp")
    assert received == {'id': 1, 'message': email.message, 'mailbox_id': 1, 'fromaddr': email.fromaddr, 'sent_via_ssl': False, 'read': False}

def test_send_receive_unreda_email(webapp, recipient, emails):
    unread_url = "/v2/mailboxes/{}/unread_emails".format(recipient.address)
    received = webapp.get_single_page(unread_url)
    assert len(received) == len(emails)
    assert [] == webapp.get_single_page(unread_url)

def test_tls(webapp, recipient, unsent_email):
    send_mail(unsent_email.fromaddr, [recipient.address], unsent_email.message, secure=True)
    [received] = webapp.get_single_page("/v2/mailboxes/{}/unread_emails".format(recipient.address))
    assert received['sent_via_ssl']

def test_mailbox_activity_gets_updated(webapp, inactive_recipient, unsent_email):
    orig = inactive_recipient.get_mailbox_obj().last_activity
    send_mail(unsent_email.fromaddr, [inactive_recipient.address], unsent_email.message)
    assert inactive_recipient.get_mailbox_obj().last_activity != orig

def test_vacuum_arg_required(webapp):
    webapp.post("/v2/vacuum").status_code == 400

def test_vacuum(webapp, inactive_recipient, recipient):
    assert len(models.Mailbox.query.all()) == 2
    webapp.post("/v2/vacuum?max_age_seconds=500")
    assert len(models.Mailbox.query.all()) == 1
    assert len(models.Email.query.all()) == 0
