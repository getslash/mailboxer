from .models import Mailbox, Email, db, emails_to_mailboxes

class Context(object):

    def __init__(self, peer):
        super(Context, self).__init__()
        self.peer = peer

def process_incoming_message(context, fromaddr, recipients, message):
    email = None
    for mailbox in Mailbox.query.filter(Mailbox.email.in_(recipients)):
        if email is None:
            email = Email(fromaddr=fromaddr, message=message)
            db.session.add(email)
        mailbox.emails.append(email)
    db.session.commit()
