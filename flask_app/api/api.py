from flask import Blueprint, request, make_response
import cjson
import functools
import httplib
from .api_signature import get_api_function_signature

api_blueprint = Blueprint("api_blueprint", __name__)

def api_handler(path, **argtypes):
    def decorator(func):
        signature = get_api_function_signature(func, argtypes)
        @functools.wraps(func)
        def new_func():
            args = request.json
            _normalize_args(args, signature)
            result = func(**request.json)
            response = make_response(cjson.encode(result))
            response.headers["Content-Type"] = "application/json"
            return response
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


@api_handler("/example_sum", a=int, b=int)
def sum(a, b):
    return {"result" : 6}
