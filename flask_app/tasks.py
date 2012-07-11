from celery import Celery
from .config import celery as celery_config

celery = Celery("tasks", broker=celery_config.BROKER_URL)

## Add your tasks here, for instance
# @celery.task
# def some_task(arg1, arg2):
#     do_something()
