from celery import Celery
from config import celeryconfig

celery = Celery("tasks", broker=celeryconfig.BROKER_URL)

## Add your tasks here, for instance
# @celery.task
# def some_task(arg1, arg2):
#     do_something()
