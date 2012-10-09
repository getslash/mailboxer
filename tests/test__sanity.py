from uuid import uuid1
import requests
import smtplib
import urlparse
from unittest import TestCase

class MailboxrTestBase(TestCase):
    def setUp(self):
        super(MailboxrTestBase, self).setUp()
        self.url_base = "http://localhost:8080"
        self.email = "{}@somedomain.com".format(uuid1())
        self.fromaddress = "{}@otherdomain.com".format(uuid1())
    def _delete(self, *args, **kwargs):
        return self._request("delete", *args, **kwargs)
    def _get(self, *args, **kwargs):
        return self._request("get", *args, **kwargs)
    def _post(self, *args, **kwargs):
        return self._request("post", *args, **kwargs)
    def _request(self, _method, *args, **kwargs):
        resp = requests.request(_method, *args, **kwargs)
        resp.raise_for_status()
        return resp

class MailboxesManagementTest(MailboxrTestBase):
    def test__create_delete_mailbox(self):
        old_mailboxes = self.get_mailboxes()
        self._post(self.url_base + "/mailboxes/", data=dict(name=self.email))
        new_mailboxes = self.get_mailboxes()
        self.assertEquals(len(new_mailboxes), len(old_mailboxes) + 1)
        self._delete(self.url_base + "/mailboxes/" + self.email)
        self.assertEquals(self.get_mailboxes(), old_mailboxes)
    def get_mailboxes(self):
        return self._get(self.url_base + "/mailboxes/").json

class EmailTest(MailboxrTestBase):
    def setUp(self):
        super(EmailTest, self).setUp()
        self._post(self.url_base + "/mailboxes/", data=dict(name=self.email))
    def test__no_emails_by_default(self):
        self.assertEquals([], self.get_all_messages())
    def test__no_unread_emails_by_default(self):
        self.assertEquals([], self.get_unread_messages())
    def test__send_receive_email(self):
        msg = "hello there\n\nbla!"
        self._send_email(msg)
        [message] = self.get_all_messages()
        self.assertEquals(str(message["message"]), msg)
    def test__unread_messages(self):
        self._send_email("email")
        self.assertEquals(len(self.get_unread_messages()), 1)
        self.assertEquals(len(self.get_unread_messages()), 0)
    def test__recreate_mailbox_deletes_emails(self):
        self._send_email("email")
        self.assertEquals(len(self.get_all_messages()), 1)
        self._delete(self.url_base + "/mailboxes/" + self.email)
        self._post(self.url_base + "/mailboxes/", data=dict(name=self.email))
        self.assertEquals(len(self.get_all_messages()), 0)
    def get_all_messages(self):
        return self._get(self.url_base + "/messages/" + self.email).json
    def get_unread_messages(self):
        return self._get(self.url_base + "/messages/" + self.email +"/unread").json
    def _send_email(self, msg):
        smtplib.SMTP("127.0.0.1", 2525).sendmail(self.fromaddress, [self.email], msg)
