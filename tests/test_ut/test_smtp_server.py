import socket
from smtplib import SMTP

from flask_app.smtp import SMTPServingThread
from flask_app.message_sink import DummyMessageSink
from ..test_utils import TestCase


class SMTPServerTest(TestCase):

    def setUp(self):
        super(SMTPServerTest, self).setUp()
        self.server_sock, self.client_sock = socket.socketpair()
        self.message_sink = DummyMessageSink()
        self.server_thread = SMTPServingThread(self.server_sock, self.message_sink)
        self.server_thread.start()
        self.addCleanup(self.server_thread.join)
        self.addCleanup(setattr, SMTP, "_get_socket", SMTP._get_socket)
        SMTP._get_socket = self._getsocket_stub

    def test_smtp(self):
        self._send_email("data")

    def _send_email(self, data, fromaddr="fromaddr@test.com", rcptto=("to@test.com",)):
        client = SMTP("server")
        client.sendmail(fromaddr, rcptto, data)
        client.quit()

    def _getsocket_stub(self, *args, **kwargs):
        return self.client_sock
