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

_RECIPIENT_REGEX = re.compile(r"^rcpt to:\s*<([^>]+)>(?:\s+.*)?$", re.I)
_MAIL_FROM_REGEX = re.compile(r"^mail from:\s*<([^>]+)>\s*$", re.I)


# Errors
_OK = (250, 'Ok')
_BYE = (221, 'Bye')
_CONTINUE = (220, 'Go ahead')
_SYNTAX_ERROR = (501, 'Syntax error')


class State(object):

    def handle_line(self, server, line, ctx):
        cmd, *_ = line.split(None, 1)
        method_name = 'handle_{}'.format(cmd.lower())
        if not hasattr(self, method_name):
            server.send(_SYNTAX_ERROR)

        return getattr(self, method_name)(server, line, ctx)

    def handle_quit(self, server, *_):
        server.send(_BYE)
        server.quit()

    def __repr__(self):
        return '[{.__class__.__name__}]'.format(self)


class Initial(State):

    def handle_ehlo(self, server, *_):
        server.sock.sendall(b'250-Mailboxer\r\n')
        extensions = [b'STARTTLS']
        for index, extension in enumerate(extensions):
            server.sock.sendall(b'250')
            if index == len(extensions) - 1:
                server.sock.sendall(b' ')
            else:
                server.sock.sendall(b'-')

            server.sock.sendall(extension)

        server.sock.sendall(b'\r\n')
        return HelloSent()


class HelloSent(State):

    def handle_mail(self, server, line, ctx):
        match = _MAIL_FROM_REGEX.match(line)
        if not match:
            server.send(_SYNTAX_ERROR)
            return

        ctx.fromaddr = match.groups()[0]
        server.send(_OK)

        return MailFromReceived()

    def handle_starttls(self, server, _, ctx):
        if ctx.ssl:
            server.send(_SYNTAX_ERROR)
            return
        server.send(_CONTINUE)
        server.sock.starttls()
        ctx.ssl = True
        server.send(_OK)
        line = server.sock.recv_line()


class MailFromReceived(State):

    def handle_rcpt(self, server, line, ctx):
        match = _RECIPIENT_REGEX.match(line)
        if not match:
            logbook.error("Invalid recipient line received: {!r}", line)
            server.send(_SYNTAX_ERROR)
            return
        recipient = match.groups()[0]
        logbook.debug('Will send to {!r}', recipient)
        ctx.recipients.append(recipient)
        server.send(_OK)

    def handle_data(self, server, line, ctx):
        if line.strip().lower() != 'data':
            server.send(_SYNTAX_ERROR)
            return

        server.send((354, "End data with <CR><LF>.<CR><LF>"))
        ctx.data = server.sock.recv_until(b"\r\n.\r\n").decode('utf-8')
        _logger.debug("Successfully processed message to {}", ctx.recipients)
        server.sink.save_message(ctx)
        server.send(_OK)
        return DataEnded()


class DataEnded(State):

    pass


class SMTPServerThread(threading.Thread):

    def __init__(self, sock, message_sink, semaphore):
        super(SMTPServerThread, self).__init__()
        self.sock = SocketHelper(sock)
        self.sink = message_sink
        self._semaphore = semaphore
        self._running = True

    def run(self):
        try:
            with closing(self.sock), logbook.StderrHandler(level=logbook.DEBUG) as h:
                h.format_string = '{record.thread}|{record.channel}: {record.message}'
                try:
                    self._run()
                except EOFError:
                    pass
                except:
                    logbook.error(
                        "Error in SMTP Serving thread", exc_info=True)
                    raise
        finally:
            self._semaphore.release()

    def _run(self):

        state = Initial()
        ctx = Context()

        self.sock.sendall(b'220 Mailboxer\r\n')

        while self._running:
            line = self.sock.recv_line()
            if not line:
                _logger.debug('Remote side has terminated the connection')
                break
            if isinstance(line, bytes):
                line = line.decode('utf-8')
            result = state.handle_line(self, line, ctx)
            if result is None:
                continue

            assert isinstance(result, State)
            _logger.debug('==> {}', result)
            state = result

        _logger.debug('Server thread quitting')
        return

    def quit(self):
        self._running = False

    def send(self, status_and_data):
        status, data = status_and_data
        if isinstance(data, str):
            data = data.encode('utf-8')
        self.sock.sendall(str(status).encode('utf-8'))
        self.sock.sendall(b" ")
        self.sock.sendall(data)
        self.sock.sendall(b'\r\n')


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
        self._sock = ssl.wrap_socket(self._sock, ssl_version=ssl.PROTOCOL_SSLv23, server_side=True,
                                     certfile=_CERT_FILE, keyfile=_KEY_FILE)  # pylint: disable=no-member

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
            _logger.debug('receving...')
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
        p, _ = self.sock.accept()

        thread = SMTPServerThread(p, self.sink, self._semaphore)
        thread.start()
        thread.join()
