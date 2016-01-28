import os
import re
import ssl
import threading
from contextlib import closing, contextmanager
from smtplib import SMTP
from socket import socket

import logbook

from .message_sink import Context, DatabaseMessageSink
from .app import create_app

_logger = logbook.Logger(__name__)

_RECIPIENT_REGEX = re.compile(b"^rcpt to:\s*<([^>]+)>(?:\s+.*)?$", re.I)
_MAIL_FROM_REGEX = re.compile(b"^mail from:\s*<([^>]+)>\s*$", re.I)

class SMTPServingThread(threading.Thread):

    def __init__(self, sock, message_sink, semaphore):
        super(SMTPServingThread, self).__init__()
        self._sock = SocketHelper(sock)
        self._sink = message_sink
        self._app = create_app()
        self._semaphore = semaphore

    def run(self):
        try:
            with closing(self._sock), logbook.StderrHandler():
                try:
                    with self._app.app_context():
                        self._run()
                except EOFError:
                    pass
                except:
                    logbook.error("Error in SMTP Serving thread", exc_info=True)
                    raise
        finally:
            self._semaphore.release()

    def _run(self):

        self._sock.sendall(b"220 Mailboxer\r\n")
        self._running = True
        ssl = False
        while self._running:

            helo_line = self._sock.recv_line()
            if helo_line.strip().lower() == b"quit":
                self._send_line(b"221 Bye")
                break
            self._send_extensions_list_and_ok()
            line = self._sock.recv_line()
            if line.strip().lower() == b"starttls":
                self._send_line(b"220 Go ahead")
                self._sock.starttls()
                helo_line = self._sock.recv_line()
                self._send_ok()
                ssl = True
                line = self._sock.recv_line()
            while self._running:
                ctx = Context()
                ctx.ssl = ssl
                ctx.fromaddr = self._parse_mail_from_line(line)
                if ctx.fromaddr is None:
                    self._send_error(501)
                    continue
                ctx.fromaddr = ctx.fromaddr.decode('utf-8')
                self._send_ok()
                line = self._sock.recv_line()
                while line.lower().startswith(b"rcpt to:"):
                    logbook.debug("Handling recipient line: {!r}", line)
                    recipient = self._parse_recipient(line)
                    logbook.debug("Recipient is {}", recipient)
                    if recipient is None:
                        self._send_error(555, "Recipient not recognized")
                        return
                    ctx.recipients.append(recipient.decode('utf-8'))
                    self._send_ok()
                    line = self._sock.recv_line()
                assert line.lower().strip() == b"data"
                self._send_line(b"354 End data with <CR><LF>.<CR><LF>")
                ctx.data = self._sock.recv_until(b"\r\n.\r\n").decode('utf-8')
                _logger.info("Successfully processed message to {}", ctx.recipients)
                self._sink.save_message(ctx)
                self._send_ok()
                line = self._sock.recv_line(allow_eof=True)
                if not line:
                    break


    def _parse_recipient(self, line):
        logbook.debug("Handling recipients: {}", line)
        match = _RECIPIENT_REGEX.match(line)
        if not match:
            logbook.error("Invalid recipient line received")
            return None
        return match.groups()[0]

    def _parse_mail_from_line(self, line):
        match = _MAIL_FROM_REGEX.match(line)
        if not match:
            logbook.error("Invalid MAIL FROM line: {!r}", line)
            return None
        return match.groups()[0]

    def _send_extensions_list_and_ok(self):
        self._send_line(b"250-Hi, Mailboxer here")
        self._send_line(b"250-STARTTLS")
        self._send_line(b"250 ok")

    def _send_ok(self):
        self._send_line(b"250 ok")

    def _send_error(self, code, error="Error"):
        _logger.error("Sending error {} ({}) to client", code, error)
        self._send_line("{0} {1}".format(code, error).encode('utf-8'))

    def _send_line(self, line):
        self._sock.sendall(line + b"\r\n")

_BUFF_SIZE = 4096
_FLASK_APP_DIR = os.path.abspath(os.path.dirname(__file__))
_CUR_DIR = os.path.abspath(os.path.dirname(__file__))
_KEY_FILE = os.path.join(_CUR_DIR, "mailboxer.key")
_CERT_FILE = os.path.join(_CUR_DIR, "mailboxer.crt")

class SocketHelper(object):

    def __init__(self, sock):
        super(SocketHelper, self).__init__()
        self._sock = sock
        self.close = self._sock.close
        self._resid = b""

    def starttls(self):
        self._sock = ssl.wrap_socket(self._sock, ssl_version=ssl.PROTOCOL_SSLv23, server_side=True, certfile=_CERT_FILE, keyfile=_KEY_FILE)

    def recv_line(self, allow_eof=False):
        return self.recv_until(b"\r\n", allow_eof=allow_eof)

    def recv_exact(self, data, case_sensitive=True):
        length = len(data)
        received = bytes()
        while length > 0:
            data = self._sock.recv(length)
            _logger.debug(" --> {!r}", data)
            if not data:
                raise EOFError()
            length -= len(data)
            received += data
        if not case_sensitive:
            data = data.lower()
            received = received.lower()
        if data != received:
            raise ProtocolError("Got invalid string: {!r}".format(received))

    def recv_until(self, token, include_token=False, allow_eof=False):
        while token not in self._resid:
            data = self._sock.recv(_BUFF_SIZE)
            _logger.debug(" --> {!r}", data)
            if not data:
                if allow_eof:
                    return self._resid
                else:
                    raise EOFError("End of data encountered")
            self._resid += data

        returned, self._resid = self._resid.split(token, 1)
        if include_token:
            returned += token
        return returned

    def sendall(self, data):
        _logger.debug(" <-- {!r}", data)
        return self._sock.sendall(data)

class ProtocolError(Exception):
    pass

_MAX_NUM_THREADS = 100

def get_semaphore():
    return threading.Semaphore(_MAX_NUM_THREADS)

@contextmanager
def smtpd_context():

    sock = socket()
    sock.bind(("127.0.0.1", 0))
    sock.listen(1)

    _, server_port = sock.getsockname()

    semaphore = get_semaphore()

    thread = ListenerThread(sock, DatabaseMessageSink(), semaphore)
    thread.start()

    client = SMTP("127.0.0.1", server_port)
    try:
        yield client
        client.quit()
    finally:
        thread.join()
        sock.close()

class ListenerThread(threading.Thread):

    def __init__(self, sock, sink, semaphore):
        super(ListenerThread, self).__init__()
        self.sock = sock
        self.sink = sink
        self._semaphore = semaphore

    def run(self):
        self._semaphore.acquire()
        p, a = self.sock.accept()

        thread = SMTPServingThread(p, self.sink, self._semaphore)
        thread.start()
        thread.join()
