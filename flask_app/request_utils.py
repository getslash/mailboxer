import functools
import httplib

from flask import request, make_response
from sqlalchemy.orm import class_mapper
import werkzeug.exceptions

class Parameter(object):
    optional = False
    def __init__(self, parameter_type):
        super(Parameter, self).__init__()
        self.type = parameter_type

class Optional(Parameter):
    optional = True

def get_request_params(schema):
    data = request.json
    convert = False
    if data is None:
        data = dict(request.form.iteritems())
        convert = True
    returned = {}
    missing = set()
    for param_name, param in schema.iteritems():
        if not isinstance(param, Parameter):
            param = Parameter(param)
        if param_name not in data and not param.optional:
            missing.add(param_name)
            continue
        param_value = data[param_name]
        if convert:
            try:
                param_value = param.type(param_value)
            except ValueError:
                error_abort_invalid_type(param_name, param_value)
        if not isinstance(param_value, param.type):
            error_abort_invalid_type(param_name, param_value)
        returned[param_name] = param_value

    if missing:
        error_abort(httplib.BAD_REQUEST, "The following parameters are missing: {}".format(", ".join(sorted(missing))))

    return returned

def error_abort_invalid_type(param_name, param_value):
    error_abort(httplib.BAD_REQUEST, "Invalid parameter value for {}: {!r}".format(param_name, param_value))

def error_abort(code, message):
    raise HTTPException(code, message)

class HTTPException(werkzeug.exceptions.HTTPException):
    def __init__(self, code, message):
        super(HTTPException, self).__init__()
        self.code = code
        self.message = message

    def get_response(self, _):
        return make_response((self.message, self.code, {}))

def takes_schema_args(**schema):
    def decorator(func):
        @functools.wraps(func)
        def new_func():
            return func(**get_request_params(schema))
        return new_func
    return decorator

def dictify_model(obj):
    return {column.key: getattr(obj, column.key) for column in class_mapper(obj.__class__).columns}
