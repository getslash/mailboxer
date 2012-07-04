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

def testing_fixture():
    with open(_TESTING_NGINX_CONF_FILE, "w") as nginx_conf:
        nginx_conf.write(_generate_testing_nginx_configuration())
    local("rm -rf {}".format(_TESTING_MONGO_DB_PATH))
    local("mkdir -p {}".format(_TESTING_MONGO_DB_PATH))

    commands = [
        "nginx -c {}".format(_TESTING_NGINX_CONF_FILE),
        "{} {}/run.py -d".format(sys.executable, os.path.dirname(__file__)),
        "mongod --auth --dbpath {}".format(_TESTING_MONGO_DB_PATH),
        ]
    _run_tmux_session("autoclave-test", commands)

def deploy():
    user = str(run("id -u -n"))

    with settings(warnings_only=True):
        sudo("supervisorctl stop {}".format(config.AUTOCLAVE_APP_NAME))

    require.deb.packages([
        "nginx", "rabbitmq-server", "mongodb", "python-virtualenv", "libevent-dev", "python-dev",
    ])
    install_root = "/opt/{}".format(config.AUTOCLAVE_APP_NAME)
    require.directory(install_root, use_sudo=True)
    sudo("chown -R {} {}".format(user, install_root))
    rsync_project(local_dir=_PROJECT_PATH + "/",
                  remote_dir="{}/src/".format(install_root),
                  delete=True, exclude=".git")
    run("virtualenv {}/env".format(install_root))
    run("{0}/env/bin/pip install -r {0}/src/pip_requirements.txt".format(install_root))
    require.supervisor.process(config.AUTOCLAVE_APP_NAME,
        command='{0}/env/bin/python {0}/src/run.py'.format(install_root),
        directory='{}/src/'.format(install_root),
        )

    put(StringIO(_generate_production_nginx_configuration(install_root)), "/etc/nginx/nginx.conf", use_sudo=True)
    sudo("service nginx restart")


def _generate_testing_nginx_configuration():
    return configuration_templates.nginx.render(tcp_port=config.AUTOCLAVE_TESTING_FRONTEND_TCP_PORT,
                                                static_root=config.AUTOCLAVE_STATIC_ROOT,
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
        local("tmux splitw -t {}".format(i))
    local("tmux selectl tiled")
    for index, command in enumerate(commands):
        local('tmux send -t {} "{}" C-m'.format(index, command))
    local("tmux attach -t {}".format(session_name))
