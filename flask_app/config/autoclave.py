import os

AUTOCLAVE_APP_NAME                     = "autoclave"
AUTOCLAVE_USER_NAME                    = AUTOCLAVE_APP_NAME
AUTOCLAVE_DEPLOY_ROOT                  = os.path.join("/opt", AUTOCLAVE_APP_NAME)
AUTOCLAVE_DEPLOY_SRC_ROOT              = os.path.join(AUTOCLAVE_DEPLOY_ROOT, "src")

AUTOCLAVE_API_ROOT                     = "/api"

AUTOCLAVE_CELERY_WORKER_SERVICE_NAME   = AUTOCLAVE_APP_NAME + "-celery"

AUTOCLAVE_DATA_ROOT                    = "/data"
AUTOCLAVE_REDIS_DB_PATH                = os.path.join(AUTOCLAVE_DATA_ROOT, "redis")
AUTOCLAVE_MONGO_DB_PATH                = os.path.join(AUTOCLAVE_DATA_ROOT, "mongo")

AUTOCLAVE_APP_TCP_PORT                 = 5353
AUTOCLAVE_DATABASE_HOST                = "127.0.0.1"
AUTOCLAVE_DEPLOYMENT_FRONTEND_TCP_PORT = 80
AUTOCLAVE_TESTING_FRONTEND_TCP_PORT    = 8080
AUTOCLAVE_STATIC_ROOT                  = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "static"))

