from smtplib import SMTP

from locust import Locust, TaskSet, task


class SMTPTask(TaskSet):
    @task
    def send_mail(self):
        smtp = SMTP('127.0.0.1', 2525)
        smtp.sendmail('rotemy@infinidat.com', ['bla@bloop.com'], 'body' * 100)

class MyLocust(Locust):
    task_set = SMTPTask
    min_wait = 5000
    max_wait = 15000
