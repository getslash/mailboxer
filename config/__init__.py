import os
import confetti

#### Edit here for basic customization
# Application name, also used for multiple other customizations
APP_NAME = "autoclave"
DATA_ROOT = "/data"
DEPLOY_ROOT = os.path.join("/opt", APP_NAME)

################################################################################

configobj = confetti.Config(dict(
    app = dict(
        name = APP_NAME,
    ),
    auth = dict(
        require_login = True,
    ),
    celery = dict(
        enabled = True,
        # the actual celery configuration is in config/celeryconfig.py
    ),
    flask = dict(
        secret_key = "",
    ),
    mongodb = dict(
        enabled = True,
        db_path = os.path.join(DATA_ROOT, "mongodb"),
        db_host = "127.0.0.1",
    ),
    rabbitmq = dict(
        enabled = True,
    ),
    redis = dict(
        enabled = True,
        db_path = os.path.join(DATA_ROOT, "redis"),
    ),
    deployment = dict(
        user = APP_NAME,
        group = APP_NAME,
        root_path = DEPLOY_ROOT,
        service_name = APP_NAME,
        virtualenv_path = os.path.join(DEPLOY_ROOT, "env"),
        src_path  = os.path.join(DEPLOY_ROOT, "src"),
        www_path  = os.path.join(DEPLOY_ROOT, "src", "www"),
        static_root = os.path.join(DEPLOY_ROOT, "src", "www", "static"),
        celeryd = dict(
            service_name = "{}-celery".format(APP_NAME),
            log_path = "/var/log/{}-celeryd.log".format(APP_NAME),
        ),
        uwsgi = dict(
            unix_socket_path = "/tmp/__{}.sock".format(APP_NAME),
            log_path = "/var/log/{}-uwsgi.log".format(APP_NAME),
            buffer_size = 16 * 1024,
        ),
        www = dict(
            production_frontend_port = 80,
            testing_frontend_port = 8080,
        )
    )
))

config = configobj.root

_overlay_filename = os.path.join(os.path.dirname(__file__), "..", "..", "config_overlay.py")
if os.path.exists(_overlay_filename):
    with open(_overlay_filename) as _overlay_file:
        exec(_overlay_file, dict(config=config))
