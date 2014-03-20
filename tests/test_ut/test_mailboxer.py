import datetime
import json
import logging

from flask_app import models

from ..test_utils import send_mail, TestCase


class SingleMailboxTest(TestCase):

    def setUp(self):
        super(SingleMailboxTest, self).setUp()
        assert len(models.Email.query.all()) == 0
        self.message = "message here"
        self.fromaddr = "someaddr@blap.com"
        self.mailbox_email = "mailbox_email@blap.com"
        self._post("/v2/mailboxes", data={"address": self.mailbox_email})

    def get_all_emails(self):
        return self._get_single_page("/v2/mailboxes/{}/emails".format(self.mailbox_email))

    def _get_single_page(self, url):
        returned = json.loads(self._get(url).data)
        self.assertEquals(returned["metadata"]["total_num_pages"], 1)
        self.assertEquals(returned["metadata"]["page"], 1)
        return returned["result"]

class MailboxTest(SingleMailboxTest):

    def test_get_mailboxes(self):
        [mailbox] = self._get_single_page("/v2/mailboxes")
        self.assertEquals(mailbox["address"], self.mailbox_email)

    def test_get_emails_empty(self):
        self.assertEquals([], self.get_all_emails())

class PaginationTest(TestCase):

    def setUp(self):
        super(PaginationTest, self).setUp()
        self.num_mailboxes = 10
        for i in range(self.num_mailboxes):
            self._post("/v2/mailboxes", data={"address": "mailbox{}@blap.com".format(i)})

    def test_pagination(self):
        response = json.loads(self._get("/v2/mailboxes?page_size=2").data)
        self.assertEquals(response["metadata"]["total_num_pages"], 5)


class EmailSendingTest(SingleMailboxTest):

    def setUp(self):
        super(EmailSendingTest, self).setUp()
        send_mail(self.fromaddr, [self.mailbox_email], self.message)

    def test_send_receive_email(self):
        [email] = self.get_all_emails()
        email.pop("timestamp")
        self.assertEquals(email, {
            "id": 1,
            "message": self.message,
            "mailbox_id": 1,
            "fromaddr": self.fromaddr,
            "sent_via_ssl": False,
            "read": False,
        })

    def test_send_receive_unred_email(self):
        l = [email for i in range(5)
             for email in self._get_single_page("/v2/mailboxes/{}/unread_emails".format(self.mailbox_email))]
        self.assertEquals(len(l), 1)
        [] = self._get_single_page("/v2/mailboxes/{}/unread_emails".format(self.mailbox_email))

class TLSTest(SingleMailboxTest):

    def setUp(self):
        super(TLSTest, self).setUp()
        send_mail(self.fromaddr, [self.mailbox_email], self.message, secure=True)

    def test_email_marked_secure(self):
        [email] = self.get_all_emails()
        self.assertTrue(email["sent_via_ssl"])


class MailboxActivityTest(SingleMailboxTest):

    def setUp(self):
        super(MailboxActivityTest, self).setUp()
        send_mail(self.fromaddr, [self.mailbox_email], self.message)
        mailbox = self._get_mailbox_db_object()
        mailbox.last_activity -= datetime.timedelta(seconds=1000)
        self.orig_last_activity = mailbox.last_activity
        models.db.session.add(mailbox)
        models.db.session.commit()

    def _get_mailbox_db_object(self):
        return models.Mailbox.query.filter(models.Mailbox.address==self.mailbox_email).one()

    def test_activity(self):
        send_mail(self.fromaddr, [self.mailbox_email], self.message)
        self.assertNotEquals(self.orig_last_activity, self._get_mailbox_db_object().last_activity)

    def test_vacuum_arg_required(self):
        assert self.app.post("/v2/vacuum").status_code == 400

    def test_vacuum(self):
        self._post("/v2/mailboxes", data={"address": "new_email@email.com"})
        self.assertEquals(
            len(models.Mailbox.query.all()), 2)
        self._post("/v2/vacuum?max_age_seconds=500")
        self.assertEquals(
            len(models.Mailbox.query.all()), 1)
        for email in models.Email.query.all():
            assert False, "Email {0} still exists".format(email.mailbox)
