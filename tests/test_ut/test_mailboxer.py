import json

from ..test_utils import send_mail, TestCase

class SingleMailboxTest(TestCase):

    def setUp(self):
        super(SingleMailboxTest, self).setUp()
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
