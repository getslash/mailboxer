from flask import Blueprint
import functools
import httplib
from .. import config
from ..utils import returns_json_response
from ..utils import param_request_handler

api_blueprint = Blueprint("api_blueprint", __name__)

def api_handler(path, **argtypes):
    def decorator(func):
        assert config.app.API_ROOT.endswith("/") ^ path.startswith("/"), "Invalid API route"
        func = param_request_handler(**argtypes)(func)
        func = returns_json_response(func)
        return api_blueprint.route(path, methods=["POST"])(func)
    return decorator

