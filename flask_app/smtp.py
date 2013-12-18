import logbook
import threading

from .message_sink import Context

_logger = logbook.Logger(__name__)

class SMTPServingThread(threading.Thread):

    def __init__(self, sock, message_sink):
        super(SMTPServingThread, self).__init__()
        self._sock = SocketHelper(sock)
        self._sink = message_sink

    def run(self):
        self._sock.sendall("220 Mailboxer\r\n")
        while True:
            ctx = Context()
            hello_line = self._sock.recv_line()
            if hello_line.strip().lower() == "quit":
                self._sock.sendall("221 Bye")
                break
            self._send_ok()
            ctx.fromaddr = self._sock.recv_line().split(":", 1)[1].strip()[1:-1]
            self._send_ok()
            line = self._sock.recv_line()
            while line.lower().startswith("rcpt to:"):
                ctx.recipients.append(line.split(":", 1)[1].strip()[1:-1])
                self._send_ok()
                line = self._sock.recv_line()
            assert line.lower().strip() == "data"
            self._sock.sendall("354 End data with <CR><LF>.<CR><LF>\r\n")
            ctx.data = self._sock.recv_until("\r\n.\r\n")
            self._send_ok()
            self._sink.save_message(ctx)

        self._sock.close()

    def _send_ok(self):
        self._sock.sendall("250 ok\r\n")

_BUFF_SIZE = 4096

class SocketHelper(object):

    def __init__(self, sock):
        super(SocketHelper, self).__init__()
        self._sock = sock
        self.close = self._sock.close
        self._resid = ""

    def recv_line(self):
        return self.recv_until("\r\n")

    def recv_exact(self, data, case_sensitive=True):
        length = len(data)
        received = ""
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

    def recv_until(self, token, include_token=False):
        while token not in self._resid:
            data = self._sock.recv(_BUFF_SIZE)
            _logger.debug(" --> {!r}", data)
            if not data:
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
