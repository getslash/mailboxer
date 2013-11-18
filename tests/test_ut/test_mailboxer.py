import json

from ..test_utils import send_mail, TestCase


class MailboxerTest(TestCase):

    def setUp(self):
        super(MailboxerTest, self).setUp()
        self.mailbox_email = "mailbox_email@blap.com"
        self._post("/v2/mailboxes", data={"email": self.mailbox_email})

    def _get_single_page(self, url):
        returned = json.loads(self._get(url).data)
        self.assertEquals(returned["metadata"]["total_num_pages"], 1)
        self.assertEquals(returned["metadata"]["page"], 1)
        return returned["result"]

    def test_get_mailboxes(self):
        [mailbox] = self._get_single_page("/v2/mailboxes")
        self.assertEquals(mailbox["email"], self.mailbox_email)
