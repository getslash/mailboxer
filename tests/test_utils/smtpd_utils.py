import threading
from contextlib import contextmanager
from smtplib import SMTP
from socket import socket

from flask_app.message_sink import DatabaseMessageSink
from flask_app.smtp import SMTPServingThread


def send_mail(fromaddr, recipients, message):
    with smtpd_context() as client:
        client.sendmail(fromaddr, recipients, message)

@contextmanager
def smtpd_context():

    sock = socket()
    sock.bind(("127.0.0.1", 0))
    sock.listen(1)

    _, server_port = sock.getsockname()

    thread = ListenerThread(sock, DatabaseMessageSink())
    thread.start()

    client = SMTP("127.0.0.1", server_port)
    try:
        yield client
        client.quit()
    finally:
        thread.join()
        sock.close()

class ListenerThread(threading.Thread):

    def __init__(self, sock, sink):
        super(ListenerThread, self).__init__()
        self.sock = sock
        self.sink = sink

    def run(self):
        p, a = self.sock.accept()
        thread = SMTPServingThread(p, self.sink)
        thread.start()
        thread.join()
