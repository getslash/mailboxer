import logbook
import datetime

from .models import Mailbox, Email, db

_logger = logbook.Logger(__name__)

class Context(object):

    def __init__(self):
        super(Context, self).__init__()
        self.peer = self.data = self.fromaddr = None
        self.ssl = False
        self.recipients = []

    def __repr__(self):
        return "<Message from {} to {}>".format(self.fromaddr, ", ".join(self.recipients))

class MessageSink(object):

    def save_message(self, ctx):
        raise NotImplementedError() # pragma: no cover


class DatabaseMessageSink(MessageSink):

    def save_message(self, ctx):
        _logger.debug("Saving email: {}", ctx)
        email = None
        now = datetime.datetime.utcnow()
        assert ctx.recipients
        for mailbox in Mailbox.query.filter(Mailbox.address.in_(ctx.recipients)):
            email = Email(fromaddr=ctx.fromaddr, message=ctx.data, sent_via_ssl=ctx.ssl, mailbox_id=mailbox.id)
            mailbox.last_activity = now
            db.session.add(mailbox)
            db.session.add(email)
        db.session.commit()

class DummyMessageSink(MessageSink):

    def __init__(self):
        super(DummyMessageSink, self).__init__()
        self.messages = []

    def save_message(self, ctx):
        self.messages.append(ctx)

