import logbook
import datetime

from .app import create_app
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

    def __init__(self):
        super(DatabaseMessageSink, self).__init__()
        self.app = create_app()

    def save_message(self, ctx):
        _logger.debug("Saving email: {}", ctx)
        with self.app.app_context():
            email = None
            now = datetime.datetime.utcnow()
            assert ctx.recipients
            db.session.flush()
            for mailbox in Mailbox.query.filter(Mailbox.address.in_(ctx.recipients)):
                email = Email(fromaddr=ctx.fromaddr, message=ctx.data, sent_via_ssl=ctx.ssl, mailbox_id=mailbox.id)
                mailbox.last_activity = now
                _logger.debug("saving email to {}", mailbox)
                db.session.add(mailbox)
                db.session.add(email)
            db.session.commit()

class DummyMessageSink(MessageSink):

    def __init__(self):
        super(DummyMessageSink, self).__init__()
        self.messages = []

    def save_message(self, ctx):
        self.messages.append(ctx)

