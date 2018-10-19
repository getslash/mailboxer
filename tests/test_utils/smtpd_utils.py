import logbook
from smtplib import SMTP


def send_mail(fromaddr, recipients, message, secure=False):
    with SMTP("localhost", 2525) as client:
        client.set_debuglevel(1)
        try:
            client.ehlo()
            if secure:
                logbook.debug("Starting TLS...")
                client.starttls()
                logbook.debug("TLS initiated")
            client.sendmail(fromaddr, recipients, message)
        except:
            logbook.error("Error while sending email", exc_info=True)
            client.close()
            raise
