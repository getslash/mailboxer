import pytest
import requests

from .test_utils import send_mail


def test_create_mailbox_twice(mailboxer, recipient):
    with pytest.raises(requests.exceptions.HTTPError) as caught:
        mailboxer.create_mailbox(recipient.address)
    assert caught.value.response.status_code == requests.codes.conflict


def test_get_mailboxes(webapp, recipient):
    mailbox = webapp.get_single_page("v2/mailboxes")[0]
    assert mailbox["address"] == recipient.address


def test_get_single_mailbox_address(webapp, recipient):
    mailbox = webapp.get(f"v2/mailboxes/{recipient.address}")["result"]
    assert mailbox["address"] == recipient.address


@pytest.mark.parametrize("subpath", ["emails", "unread_emails"])
def test_unknown_mailbox_emails_not_found(webapp, subpath):
    resp = webapp.get("v2/mailboxes/nonexisting/" + subpath, raw_response=True)
    assert resp.status_code == requests.codes.not_found


def test_get_all_emails(mailboxer, recipient, emails):
    received = mailboxer.get_emails(recipient.address)
    assert len(received) == len(emails)
    for r, e in zip(received, emails):
        assert r.fromaddr == e.fromaddr


def test_get_mailboxes_pagination(webapp, recipients, page_size):
    result = webapp.get("v2/mailboxes", params={"page_size": 100})


def test_send_receive_email(webapp, recipient, email):
    received_emails = webapp.get_single_page(
        "v2/mailboxes/{}/emails".format(recipient.address)
    )
    assert len(received_emails) == 1
    [received] = received_emails
    received.pop("timestamp")
    received.pop("mailbox_id")
    received.pop("id")
    assert received == {
        "message": email.message,
        "fromaddr": email.fromaddr,
        "sent_via_ssl": False,
        "read": False,
    }


def test_send_receive_unreda_email(webapp, recipient, emails):
    unread_url = "v2/mailboxes/{}/unread_emails".format(recipient.address)
    received = webapp.get_single_page(unread_url)
    assert len(received) == len(emails)
    assert [] == webapp.get_single_page(unread_url)


def test_tls(webapp, recipient, unsent_email):
    send_mail(
        unsent_email.fromaddr, [recipient.address], unsent_email.message, secure=True
    )
    [received] = webapp.get_single_page(
        "v2/mailboxes/{}/unread_emails".format(recipient.address)
    )
    assert received["sent_via_ssl"]


def test_mailbox_activity_gets_updated(webapp, recipient, unsent_email):
    def get_last_activity():
        return webapp.get(f"v2/mailboxes/{recipient.address}")

    orig = get_last_activity()
    send_mail(unsent_email.fromaddr, [recipient.address], unsent_email.message)
    assert get_last_activity() != orig


def test_vacuum(webapp, recipient):
    webapp.post(f"v2/_debug/make_inactive/{recipient.address}")
    url = f"v2/mailboxes/{recipient.address}"
    assert recipient.address == webapp.get(url)["result"]["address"]
    webapp.post("v2/vacuum")
    assert webapp.get_raw(url).status_code == requests.codes.not_found


@pytest.mark.parametrize("page_size", [1, 2, 5, 10, 20])
def test_pagination(webapp, recipient, email, page_size):
    num_emails = 10

    for i in range(num_emails):
        send_mail(email.fromaddr, [recipient.address], email.message)

    def get_page(page_num, page_size=2):
        result = webapp.get(
            f"v2/mailboxes/{recipient.address}/emails",
            params={"page": page_num, "page_size": page_size},
        )
        return [email["id"] for email in result["result"]]

    expected_emails = get_page(1, num_emails)

    actual = []

    page_num = 1
    while len(actual) < len(expected_emails):
        page = get_page(page_num, page_size)
        page_num += 1
        assert page
        actual.extend(page)

    assert actual[: len(expected_emails)] == expected_emails
