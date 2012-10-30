import cjson
import flask
import functools
from .function_signature import get_function_signature

def render_template(template, **kwargs):
    return flask.render_template(template,
                                 session=flask.session,
                                 request=flask.request, **kwargs)

def returns_json_response(func):
    @functools.wraps(func)
    def new_func(*args, **kwargs):
        result = func(*args, **kwargs)
        response = flask.make_response(cjson.encode(result))
        response.headers["Content-Type"] = "application/json"
        return response
    return new_func

def param_request_handler(**argtypes):
    """
    Automatically passes parameters to a flask request handler from the request itself, based on expected types

    Usage:

    >>> @app.route("/some/path", methods=["POST"])
    ... @param_request_handler(a=int, b=str, c=float)
    ... def handler(a, b, c=None):
    ...    ...

    The above will require 'a' and 'b' to be present in the post, and will allow 'c' to be omitted. In all cases, the parameter types
    will be checked before entering the handler
    """
    def decorator(func):
        signature = get_function_signature(func, argtypes)
        @functools.wraps(func)
        def new_func():
            args = flask.request.json
            if args is None:
                args = {k : flask.request.form[k][0] for k, v in flask.request.form.iteritems()}
            _normalize_args(args, signature)
            return func(**args)
        return new_func
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
