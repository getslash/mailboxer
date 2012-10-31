from datetime import timedelta

BROKER_URL="amqp://guest:guest@localhost:5672//"

CELERY_IMPORTS = ("flask_app.tasks", )

CELERYBEAT_SCHEDULE = {
# "runs-every-30-seconds" : {
#    "task" : "flask_app.tasks.some_task",
#    "schedule" : timedelta(seconds=30),
#    "args" : ("arg1", "arg2"),
#}
}
