import os
import sys
from fabric.api import *
from fabric.contrib.project import rsync_project
import fabtools
from config import config
from .parameters import LOCAL_PROJECT_ROOT
from . import _templates

def deploy_to_vagrant():
    with lcd(os.path.dirname(__file__)):
        local("vagrant up")
        with settings(user="vagrant", host_string="127.0.0.1", port=2222, key_filename="~/.vagrant.d/insecure_private_key"):
            deploy_to_server()

def deploy_to_server():
    _ensure_user()
    if config.redis.enabled:
        _deploy_redis()
    if config.mongodb.enabled:
        _deploy_mongo()
    if config.rabbitmq.enabled:
        _deploy_rabbitmq()
    _deploy_flask_app()
    if config.celery.enabled:
        _deploy_celeryd()
    _deploy_nginx()

def _ensure_user():
    fabtools.require.user(config.deployment.user, home="/home/{0}".format(config.deployment.user))

def _deploy_redis():
    _ensure_directory(config.redis.db_path)
    fabtools.require.deb.packages(["redis-server"])
    fabtools.require.file(
        "/etc/redis.conf",
        contents="dir {}".format(config.redis.db_path),
        use_sudo=True,
    )
    fabtools.service.start("redis-server")


def _deploy_mongo():
    _ensure_directory(config.mongodb.db_path)
    fabtools.require.deb.packages(["mongodb"])
    fabtools.require.file(
        "/etc/mongod.conf",
        contents="""
# Store data in /usr/local/var/mongodb instead of the default /data/db
dbpath = {}

# Only accept local connections
bind_ip = 127.0.0.1""".format(config.mongodb.db_path),
        use_sudo=True)
    fabtools.service.start("mongodb")

def _deploy_rabbitmq():
    fabtools.require.deb.packages(["rabbitmq-server"])

def _deploy_flask_app():
    _stop_flask_app()
    _ensure_directory(config.deployment.root_path)
    _deploy_app_virtualenv()
    _deploy_gevent_requirements()
    _deploy_sync_project_source()
    _deploy_install_app_requirements()
    _deploy_uwsgi_service()
    _start_flask_app()

def _deploy_celeryd():
    _setup_log_rotation(
        config.deployment.celeryd.log_path,
        config.deployment.celeryd.service_name,
    )
    fabtools.require.supervisor.process(
        config.deployment.celeryd.service_name,
        command="{0}/bin/celeryd --logfile={1} -B --config=flask_app.config.celery".format(config.deployment.virtualenv_path, config.deployment.celeryd.log_path),
        directory=config.deployment.www_path,
        user=config.deployment.user,
        )

def _deploy_nginx():
    fabtools.require.deb.packages(["nginx"])
    fabtools.require.file(
        "/etc/nginx/nginx.conf",
        contents=_deploy_nginx_configuration(),
        use_sudo=True,
    )
    _deploy_nginx_configuration()
    fabtools.service.restart("nginx")

def _deploy_nginx_configuration():
    return _templates.nginx.render(
        tcp_port=config.deployment.www.production_frontend_port,
        static_root=config.deployment.static_root,
        uwsgi_socket_path=config.deployment.uwsgi.unix_socket_path,
        daemon=True, config=config)

############################# Flask app deployment #############################
def _stop_flask_app():
    _flask_app_service_action("stop")

def _start_flask_app():
    _flask_app_service_action("start")

def _flask_app_service_action(action):
    services = [
        config.deployment.service_name,
    ]
    if config.celery.enabled:
        services.append(config.deployment.celeryd.service_name)
    for service in services:
        with settings(warn_only=True):
            sudo("supervisorctl {} {}".format(action, service))

def _run_as_app_user(cmd):
    sudo(cmd, user=config.deployment.user)

def _deploy_app_virtualenv():
    fabtools.require.deb.packages(["python-virtualenv"])
    virtualenv_path = "{}/env".format(config.deployment.root_path)
    with cd("/tmp"): # various commands might fail saving data to /root...
        if not fabtools.files.is_dir(virtualenv_path):
            _run_as_app_user("virtualenv --distribute {}".format(virtualenv_path))

def _deploy_gevent_requirements():
    fabtools.require.deb.packages([
        "libevent-dev", "python-dev", "build-essential"
    ])

def _deploy_sync_project_source():
    tmp_dir = "/tmp/__autoclave_project_sync"
    rsync_project(local_dir= LOCAL_PROJECT_ROOT + "/",
                  remote_dir=tmp_dir,
                  delete=True, exclude=".git")
    _run_as_app_user("rsync -rv {}/ {}/".format(tmp_dir, config.deployment.src_path))

def _deploy_install_app_requirements():
    with cd("/tmp"):
        _run_as_app_user(
            "{0}/bin/pip install -r {1}/config/pip_requirements.txt".format(
                config.deployment.virtualenv_path,
                config.deployment.src_path))

def _deploy_uwsgi_service():
    _setup_log_rotation(
        config.deployment.uwsgi.log_path,
        config.deployment.service_name)

    fabtools.require.supervisor.process(
        config.app.name,
        command=("{config.deployment.virtualenv_path}/bin/uwsgi -b {config.deployment.uwsgi.buffer_size} "
                 "--pythonpath={config.deployment.src_path} --pythonpath={config.deployment.www_path} "
                 "--chmod-socket 666 -H {config.deployment.root_path}/env -w flask_app.app:app "
                 "-s {config.deployment.uwsgi.unix_socket_path} --logto={config.deployment.uwsgi.log_path}").format(config=config),
        directory=config.deployment.www_path,
        user=config.deployment.user,
    )

################################ Misc. utilities ###############################

def _ensure_directory(directory):
    fabtools.require.directory(directory, use_sudo=True)
    sudo("chown -R {config.deployment.user}:{config.deployment.group} {dir}".format(config=config, dir=directory))

def _setup_log_rotation(log_path, service_name):
    uwsgi_logrotate_file_path = "/etc/logrotate.d/{0}".format(service_name)
    fabtools.require.file(uwsgi_logrotate_file_path,
                 use_sudo=True,
                 contents="""\
{log_path} {{
    rotate 10
    daily
    compress
    missingok
    create 640 {config.deployment.user} {config.deployment.group}
    postrotate
        supervisorctl restart {service_name}
    endscript
}}""".format(log_path=log_path, service_name=service_name, config=config))

    # we both call logrotate and "touch" the log file. The former is for cases where the log already existed
    # while the latter is for cases in which the log file did not exist before
    sudo("touch {log_path} && chown {config.deployment.user}:{config.deployment.group} {log_path}".format(config=config, log_path=log_path))
    sudo("logrotate -f {0}".format(log_path))

################################################################################
