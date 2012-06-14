import os
import sys
import subprocess
from fabric.api import *
from flask_app import config
import configuration_templates

_TESTING_MONGO_DB_PATH = "/tmp/__autoclave_testing_mongodb"
_TESTING_NGINX_CONF_FILE = "/tmp/__autoclave_testing_nginx.conf"

def compile_css():
    local("lessc static_src/style.less > static/css/style.css")

def testing_fixture():
    with open(_TESTING_NGINX_CONF_FILE, "w") as nginx_conf:
        nginx_conf.write(_generate_testing_nginx_configuration())
    local("rm -rf {}".format(_TESTING_MONGO_DB_PATH))
    local("mkdir -p {}".format(_TESTING_MONGO_DB_PATH))

    left_commands = [
        "nginx -c {}".format(_TESTING_NGINX_CONF_FILE),
        "{} {}/run.py -d".format(sys.executable, os.path.dirname(__file__)),
        ]
    right_commands = [
        "mongod --auth --dbpath {}".format(_TESTING_MONGO_DB_PATH),
        ]
    _run_tmux_session(left_commands, right_commands)

def _generate_testing_nginx_configuration():
    return configuration_templates.nginx.render(tcp_port=config.AUTOCLAVE_TESTING_FRONTEND_TCP_PORT,
                                                daemon=False, config=config)

def _run_tmux_session(left_commands, right_commands):
    session = ''
    if right_commands:
        session += 'tmux selectp -t 0; tmux splitw -hd -p 50 \"%s\"; ' % right_commands[-1]
    for index, command in enumerate(right_commands[:-1]):
        session += 'tmux selectp -t 1; tmux splitw -d -p %i \"%s\"; ' % (
            100 / (len(right_commands) - index),
            command
    )

    for index, command in enumerate(left_commands[1:]):
        session += 'tmux selectp -t 0; tmux splitw -d -p %i \"%s\"; ' % (
            100 / (len(left_commands) - index),
            command
    )
    if left_commands:
        session += left_commands[0]
    args = [
        'tmux',
        'new-session',
        session,
        ]
    subprocess.call(args)
