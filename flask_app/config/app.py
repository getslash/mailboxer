import os

APP_NAME                     = "autoclave"
USER_NAME                    = APP_NAME
GROUP_NAME                   = USER_NAME
DEPLOY_ROOT                  = os.path.join("/opt", APP_NAME)
DEPLOY_SRC_ROOT              = os.path.join(DEPLOY_ROOT, "src")

UWSGI_UNIX_SOCK_PATH         = "/tmp/__{}.sock".format(APP_NAME)
UWSGI_LOG_PATH               = "/var/log/{}-uwsgi.log".format(APP_NAME)
UWSGI_BUFFER_SIZE            = 16 * 1024

REQUIRE_LOGIN                = True

CELERY_WORKER_SERVICE_NAME   = APP_NAME + "-celery"

DATA_ROOT                    = "/data"
REDIS_DB_PATH                = os.path.join(DATA_ROOT, "redis")
MONGO_DB_PATH                = os.path.join(DATA_ROOT, "mongo")

DATABASE_HOST                = "127.0.0.1"
DEPLOYMENT_FRONTEND_TCP_PORT = 80
TESTING_FRONTEND_TCP_PORT    = 8080
STATIC_ROOT                  = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "static"))

