from ..test_utils import TestCase, smtpd_context
from flask_app import models
from flask_app.messages import process_incoming_message, Context

class MessageProcessingTest(TestCase):

    def setUp(self):
        super(MessageProcessingTest, self).setUp()
        self.email = "somerecipient@someaddress.com"
        self.fromaddr = "somesender@someaddress.com"
        self.message = "This is a message here"
        models.db.session.add(models.Mailbox(email=self.email))
        models.db.session.commit()

    def test_incoming_message_no_mailbox_match(self):
        with smtpd_context() as client:
            client.sendmail(self.fromaddr, ["noninteresting_address@email.com"], self.message)
        self.assertEquals(models.Email.query.count(), 0)

    def test_incoming_message(self):
        with smtpd_context() as client:
            client.sendmail(self.fromaddr, [self.email, "blap@bloop.com"], self.message)
        [email] = models.Email.query.all()

