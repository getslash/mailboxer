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
        "mongod --auth --dbpath {}".format(_TESTING_MONGO_DB_PATH),
        "redis-server",
        "cd {} && {} -l DEBUG -B --config=flask_app.config.celery".format(src_root, celeryd_executable),
        "rabbitmq-server",
        ]
    _run_tmux_session("autoclave-test", commands)


def deploy_vagrant():
    local("vagrant up")
    with settings(user="vagrant", host_string="127.0.0.1", port=2222, key_filename="~/.vagrant.d/insecure_private_key"):
        deploy()

def deploy():
    _deploy_stop_previous_instance()

    _deploy_ensure_user()
    for directory in (
            config.app.DEPLOY_ROOT,
            config.app.DATA_ROOT,
            config.app.REDIS_DB_PATH,
            config.app.MONGO_DB_PATH,
        ):
        _deploy_ensure_dir(directory)

    _deploy_setup_redis()
    _deploy_setup_mongo()

    require.deb.packages([
        "nginx", "rabbitmq-server", "python-virtualenv", "libevent-dev", "python-dev",
    ])

    _deploy_sync_project()

    virtualenv_path = "{}/env".format(config.app.DEPLOY_ROOT)
    if not fabtools.files.is_dir(virtualenv_path):
        with cd("/tmp"): # virtualenv has a bug when running from /root
            _deploy_run_as_autoclave_user("virtualenv --distribute {}".format(virtualenv_path))
    _deploy_run_as_autoclave_user("{0}/env/bin/pip install -r {0}/src/pip_requirements.txt".format(config.app.DEPLOY_ROOT))

    require.supervisor.process(config.app.APP_NAME,
        command="{0}/env/bin/uwsgi --chmod-socket 666 -H {0}/env -w flask_app.app:app -s {1}".format(config.app.DEPLOY_ROOT, config.app.UWSGI_UNIX_SOCK_PATH),
        directory=config.app.DEPLOY_SRC_ROOT,
        user=config.app.USER_NAME,
        )

    require.supervisor.process(config.app.CELERY_WORKER_SERVICE_NAME,
        command="{0}/env/bin/celeryd -B --config=flask_app.config.celery".format(config.app.DEPLOY_ROOT),
        directory=config.app.DEPLOY_SRC_ROOT,
        user=config.app.USER_NAME,
        )

    put(StringIO(_generate_production_nginx_configuration(config.app.DEPLOY_ROOT)), "/etc/nginx/nginx.conf", use_sudo=True)
    fabtools.service.restart("nginx")
    _deploy_start_instance()

def _deploy_stop_previous_instance():
    _deploy_supervisord_action("stop")

def _deploy_start_instance():
    _deploy_supervisord_action("start")

def _deploy_supervisord_action(action):
    for service in (
            config.app.APP_NAME,
            config.app.CELERY_WORKER_SERVICE_NAME,
        ):
        with settings(warn_only=True):
            sudo("supervisorctl {} {}".format(action, service))

def _deploy_ensure_user():
    require.user(config.app.USER_NAME)
def _deploy_ensure_dir(directory):
    require.directory(directory, use_sudo=True)
    sudo("chown -R {} {}".format(config.app.USER_NAME, directory))

def _deploy_setup_redis():
    require.deb.packages(["redis-server"])
    put(StringIO("dir {}".format(config.app.REDIS_DB_PATH)), "/etc/redis.conf", use_sudo=True)
    fabtools.service.restart("redis-server")

def _deploy_setup_mongo():
    require.deb.packages(["mongodb"])
    put(StringIO("""
# Store data in /usr/local/var/mongodb instead of the default /data/db
dbpath = {}

# Only accept local connections
bind_ip = 127.0.0.1""".format(config.app.MONGO_DB_PATH)), "/etc/mongod.conf", use_sudo=True)
    fabtools.service.restart("mongodb")

def _deploy_sync_project():
    tmp_dir = "/tmp/__autoclave_project_sync"
    rsync_project(local_dir=_PROJECT_PATH + "/",
                  remote_dir=tmp_dir,
                  delete=True, exclude=".git")
    _deploy_run_as_autoclave_user("rsync -rv {}/ {}/".format(tmp_dir, config.app.DEPLOY_SRC_ROOT))

def _deploy_run_as_autoclave_user(cmd):
    sudo(cmd, user=config.app.USER_NAME)

def _generate_testing_nginx_configuration():
    return configuration_templates.nginx.render(tcp_port=config.app.TESTING_FRONTEND_TCP_PORT,
                                                static_root=config.app.STATIC_ROOT,
                                                daemon=False, config=config)
def _generate_production_nginx_configuration(installation_root):
    return configuration_templates.nginx.render(tcp_port=80,
                                                static_root="{}/src/flask_app/static".format(installation_root),
                                                uwsgi_socket_path=config.app.UWSGI_UNIX_SOCK_PATH,
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
