from uuid import uuid1
import httplib
import requests
import smtplib
import urlparse
from unittest import TestCase
from config import config
from ..test_utils import config_utils
from .deployment_test import DeploymentTest

class MailboxrTestBase(DeploymentTest):
    def setUp(self):
        super(MailboxrTestBase, self).setUp()
        self.email = "{}@somedomain.com".format(uuid1())
        self.fromaddress = "{}@otherdomain.com".format(uuid1())
    def _delete(self, *args, **kwargs):
        return self._request("delete", *args, **kwargs)
    def _get(self, *args, **kwargs):
        return self._request("get", *args, **kwargs)
    def _post(self, *args, **kwargs):
        return self._request("post", *args, **kwargs)
    def _request(self, _method, *args, **kwargs):
        resp = self.request(_method, *args, **kwargs)
        resp.raise_for_status()
        return resp

class MailboxesManagementTest(MailboxrTestBase):
    def test__create_delete_mailbox(self):
        old_mailboxes = self.get_mailboxes()
        self._post("/mailboxes/", data=dict(name=self.email))
        new_mailboxes = self.get_mailboxes()
        self.assertEquals(len(new_mailboxes), len(old_mailboxes) + 1)
        self._delete("/mailboxes/" + self.email)
        self.assertEquals(self.get_mailboxes(), old_mailboxes)
    def test__cannot_create_star_mailbox(self):
        with self.assertRaises(requests.HTTPError) as caught:
            self._post("/mailboxes/", data=dict(name="*"))
        self.assertEquals(caught.exception.response.status_code, httplib.BAD_REQUEST)
    def get_mailboxes(self):
        return self._get("/mailboxes/").json()

class EmailTest(MailboxrTestBase):
    def setUp(self):
        super(EmailTest, self).setUp()
        self._post("/mailboxes/", data=dict(name=self.email))
    def test__no_emails_by_default(self):
        self.assertEquals([], self.get_all_messages())
    def test__no_unread_emails_by_default(self):
        self.assertEquals([], self.get_unread_messages())
    def test__send_receive_email(self):
        msg = "hello there\n\nbla!"
        self._send_email(msg)
        for retry in range(3):
            [message] = self.get_all_messages()
            self.assertEquals(str(message["message"]), msg)
    def test__unread_messages(self):
        self._send_email("email")
        self.assertEquals(len(self.get_unread_messages()), 1)
        self.assertEquals(len(self.get_unread_messages()), 0)
    def test__unread_messages_paging(self):
        for i in range(2):
            for j in range(config.max_unread_messages_page_size):
                self._send_email("email")
        for i in range(2):
            unread = self.get_unread_messages()
            self.assertEquals(len(unread), config.max_unread_messages_page_size)
        self.assertEquals(self.get_unread_messages(), [])
    def test__recreate_mailbox_deletes_emails(self):
        self._send_email("email")
        self.assertEquals(len(self.get_all_messages()), 1)
        self._delete("/mailboxes/" + self.email)
        self._post("/mailboxes/", data=dict(name=self.email))
        self.assertEquals(len(self.get_all_messages()), 0)
    def get_all_messages(self):
        return self._get("/messages/" + self.email).json()
    def get_unread_messages(self):
        return self._get("/messages/" + self.email +"/unread").json()
    def _send_email(self, msg):
        smtplib.SMTP("127.0.0.1", config_utils.get_config_int("smtp_port", 2525)).sendmail(self.fromaddress, [self.email], msg)
