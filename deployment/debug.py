import os
import sys
from fabric.api import *
from config import config
from .tmux import run_tmux_session
from .parameters import LOCAL_PROJECT_ROOT

_TESTING_MONGO_DB_PATH = "/tmp/__{}.db".format(config.app.name)

def debug():
    """
    Runs a tmux session with all services in different panes, enabling you to quickly debug,
    examine and restart parts of your app quickly.
    """
    _purge_previous_dirs()

    commands = ["PYTHONPATH={0} {1} {0}/deployment/libexec/run.py -d".format(LOCAL_PROJECT_ROOT, sys.executable)]
    if config.mongodb.enabled:
        commands.append("mongod --auth --dbpath {}".format(_TESTING_MONGO_DB_PATH))
    if config.redis.enabled:
        commands.append("redis-server")
    if config.rabbitmq.enabled:
        commands.append("rabbitmq-server")
    if config.celery.enabled:
        celeryd_path = _find_executable("celeryd")
        commands.append("cd {0}/www && PYTHONPATH={0} {1} -l DEBUG -B --config=config.celeryconfig".format(LOCAL_PROJECT_ROOT, celeryd_path))
    commands.append("{} {}/mailboxer_smtpd.py -vv -p 2525".format(sys.executable, LOCAL_PROJECT_ROOT))
    run_tmux_session("{}-test".format(config.app.name), commands)

def _find_executable(name):
    return local("which {0}".format(name), capture=True).stdout

def _purge_previous_dirs():
    local("rm -rf {}".format(_TESTING_MONGO_DB_PATH))
    local("mkdir -p {}".format(_TESTING_MONGO_DB_PATH))
