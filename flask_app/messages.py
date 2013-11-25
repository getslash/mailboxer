from .models import Mailbox, Email, db

class Context(object):

    def __init__(self, peer):
        super(Context, self).__init__()
        self.peer = peer

def process_incoming_message(context, fromaddr, recipients, message):
    email = None
    for mailbox in Mailbox.query.filter(Mailbox.address.in_(recipients)):
        email = Email(fromaddr=fromaddr, message=message, sent_via_ssl=False, mailbox_id=mailbox.id)
        db.session.add(email)
    db.session.commit()
