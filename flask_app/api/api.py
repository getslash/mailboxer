from flask import Blueprint, request, make_response
import cjson
import functools
import httplib
from .api_signature import get_api_function_signature

api_blueprint = Blueprint("api_blueprint", __name__)

def returns_json(func):
    @functools.wraps(func)
    def new_func():
        result = func()
        response = make_response(cjson.encode(result))
        response.headers["Content-Type"] = "application/json"
        return response
    return new_func

def api_handler(path, **argtypes):
    def decorator(func):
        signature = get_api_function_signature(func, argtypes)
        @functools.wraps(func)
        @returns_json
        def new_func():
            args = request.json
            _normalize_args(args, signature)
            return func(**args)
        return api_blueprint.route(path, methods=["POST"])(new_func)
    return decorator

def _normalize_args(args, signature):
    missing = set(signature.argtypes)
    for key in set(args):
        value = args[key]
        argument_type = signature.argtypes.get(key)
        if argument_type is None:
            abort(httplib.BAD_REQUEST)
        try:
            value = argument_type(value)
        except ValueError:
            abort(httplib.BAD_REQUEST)
        args[key] = value
        missing.remove(key)
    if missing - signature.optionals:
        abort(httplib.BAD_REQUEST)
