import logbook

from flask_app.smtp import smtpd_context


def send_mail(fromaddr, recipients, message, secure=False):
    with smtpd_context() as client:
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
