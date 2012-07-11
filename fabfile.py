import os
import sys
import subprocess
from StringIO import StringIO
from fabric.api import *
from fabric.contrib.project import rsync_project
import fabtools
from fabtools import require
from flask_app import config
import configuration_templates

_PROJECT_PATH = os.path.abspath(os.path.dirname(__file__))

_TESTING_MONGO_DB_PATH = "/tmp/__autoclave_testing_mongodb"
_TESTING_NGINX_CONF_FILE = "/tmp/__autoclave_testing_nginx.conf"

def compile_css():
    local("lessc --compress static_src/style.less > static/css/style.css")

def debug():
    with open(_TESTING_NGINX_CONF_FILE, "w") as nginx_conf:
        nginx_conf.write(_generate_testing_nginx_configuration())
    local("rm -rf {}".format(_TESTING_MONGO_DB_PATH))
    local("mkdir -p {}".format(_TESTING_MONGO_DB_PATH))

    celeryd_executable = str(local("which celeryd", capture=True))
    assert os.path.exists(celeryd_executable)

    src_root = os.path.dirname(__file__)

    commands = [
        "{} {}/run.py -d".format(sys.executable, src_root),
        "nginx -c {}".format(_TESTING_NGINX_CONF_FILE),
        "mongod --auth --dbpath {}".format(_TESTING_MONGO_DB_PATH),
        "redis-server",
        "cd {} && {} -l DEBUG -B --config=flask_app.config.celery".format(src_root, celeryd_executable),
        "rabbitmq-server",
        ]
    _run_tmux_session("autoclave-test", commands)

def deploy():
    _deploy_stop_previous_instance()

    _deploy_ensure_user()
    for directory in (
            config.autoclave.AUTOCLAVE_DEPLOY_ROOT,
            config.autoclave.AUTOCLAVE_DATA_ROOT,
            config.autoclave.AUTOCLAVE_REDIS_DB_PATH,
            config.autoclave.AUTOCLAVE_MONGO_DB_PATH,
        ):
        _deploy_ensure_dir(directory)

    _deploy_setup_redis()
    _deploy_setup_mongo()

    require.deb.packages([
        "nginx", "rabbitmq-server", "python-virtualenv", "libevent-dev", "python-dev",
    ])

    _deploy_sync_project()

    _deploy_run_as_autoclave_user("virtualenv {}/env".format(config.autoclave.AUTOCLAVE_DEPLOY_ROOT))
    _deploy_run_as_autoclave_user("{0}/env/bin/pip install -r {0}/src/pip_requirements.txt".format(config.autoclave.AUTOCLAVE_DEPLOY_ROOT))

    require.supervisor.process(config.autoclave.AUTOCLAVE_APP_NAME,
        command='{0}/env/bin/python {0}/src/run.py'.format(config.autoclave.AUTOCLAVE_DEPLOY_ROOT),
        directory=config.autoclave.AUTOCLAVE_DEPLOY_SRC_ROOT,
        user=config.autoclave.AUTOCLAVE_USER_NAME,
        )

    require.supervisor.process(config.autoclave.AUTOCLAVE_CELERY_WORKER_SERVICE_NAME,
        command="{0}/env/bin/celeryd -B --config=flask_app.config.celery".format(config.autoclave.AUTOCLAVE_DEPLOY_ROOT),
        directory=config.autoclave.AUTOCLAVE_DEPLOY_SRC_ROOT,
        user=config.autoclave.AUTOCLAVE_USER_NAME,
        )

    put(StringIO(_generate_production_nginx_configuration(config.autoclave.AUTOCLAVE_DEPLOY_ROOT)), "/etc/nginx/nginx.conf", use_sudo=True)
    fabtools.service.restart("nginx")


def _deploy_stop_previous_instance():
    for service in (
            config.autoclave.AUTOCLAVE_APP_NAME,
            config.autoclave.AUTOCLAVE_CELERY_WORKER_SERVICE_NAME,
        ):
        with settings(warn_only=True):
            sudo("supervisorctl stop {}".format(config.autoclave.AUTOCLAVE_APP_NAME))

def _deploy_ensure_user():
    require.user(config.autoclave.AUTOCLAVE_USER_NAME)
def _deploy_ensure_dir(directory):
    require.directory(directory, use_sudo=True)
    sudo("chown -R {} {}".format(config.autoclave.AUTOCLAVE_USER_NAME, directory))

def _deploy_setup_redis():
    require.deb.packages(["redis-server"])
    put(StringIO("dir {}".format(config.autoclave.AUTOCLAVE_REDIS_DB_PATH)), "/etc/redis.conf", use_sudo=True)
    fabtools.service.restart("redis-server")

def _deploy_setup_mongo():
    require.deb.packages(["mongodb"])
    put(StringIO("""
# Store data in /usr/local/var/mongodb instead of the default /data/db
dbpath = {}

# Only accept local connections
bind_ip = 127.0.0.1""".format(config.autoclave.AUTOCLAVE_MONGO_DB_PATH)), "/etc/mongod.conf", use_sudo=True)
    fabtools.service.restart("mongodb")

def _deploy_sync_project():
    tmp_dir = "/tmp/__autoclave_project_sync"
    rsync_project(local_dir=_PROJECT_PATH + "/",
                  remote_dir=tmp_dir,
                  delete=True, exclude=".git")
    _deploy_run_as_autoclave_user("rsync -rv {}/ {}/".format(tmp_dir, config.autoclave.AUTOCLAVE_DEPLOY_SRC_ROOT))

def _deploy_run_as_autoclave_user(cmd):
    sudo(cmd, user=config.autoclave.AUTOCLAVE_USER_NAME)

def _generate_testing_nginx_configuration():
    return configuration_templates.nginx.render(tcp_port=config.autoclave.AUTOCLAVE_TESTING_FRONTEND_TCP_PORT,
                                                static_root=config.autoclave.AUTOCLAVE_STATIC_ROOT,
                                                daemon=False, config=config)
def _generate_production_nginx_configuration(installation_root):
    return configuration_templates.nginx.render(tcp_port=80,
                                                static_root="{}/src/static".format(installation_root),
                                                daemon=True, config=config)


def _run_tmux_session(session_name, commands):
    with settings(warn_only=True):
        if local("tmux attach -t {}".format(session_name)).succeeded:
            return
    local("tmux new -d -s {}".format(session_name))
    for i in range(len(commands)-1):
        local("tmux splitw -t {} {}".format(i-1, "-h" if i % 2 else ""))
    local("tmux selectl main-vertical")
    for index, command in enumerate(commands):
        local('tmux send -t {} "{}" C-m'.format(index, command))
    local("tmux attach -t {}".format(session_name))
