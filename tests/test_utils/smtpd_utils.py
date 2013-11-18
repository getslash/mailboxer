import asyncore
import select
import threading
from contextlib import contextmanager
from smtplib import SMTP

import errno
from flask_app.services import smtpd


def send_mail(fromaddr, recipients, message):
    with smtpd_context() as client:
        client.sendmail(fromaddr, recipients, message)

@contextmanager
def smtpd_context():
    server = smtpd.initialize_server(0, secure=False)
    _, server_port = server.socket.getsockname()

    asyncore_thread = threading.Thread(target=_asyncore_thread)

    asyncore_thread.start()
    client = SMTP("127.0.0.1", server_port)
    try:
        yield client
        client.quit()
    finally:
        asyncore.close_all()
        asyncore_thread.join()

def _asyncore_thread():
    try:
        asyncore.loop()
    except select.error as e:
        if e.args[0] != errno.EBADF:
            raise
