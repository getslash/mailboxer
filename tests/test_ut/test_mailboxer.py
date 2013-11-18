import json

from ..test_utils import TestCase, send_mail

class MailboxerTest(TestCase):

    def setUp(self):
        super(MailboxerTest, self).setUp()
        self.mailbox_name = "mailbox_name"
        self._post("/v2/mailboxes", data=json.dumps({"name": self.mailbox_name}))

    def test_get_mailboxes(self):
        pass
