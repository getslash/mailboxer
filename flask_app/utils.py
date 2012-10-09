import cjson
import flask
import functools

def render_template(template, **kwargs):
    return flask.render_template(template, request=flask.request, **kwargs)

def returns_json(func):
    @functools.wraps(func)
    def new_func(*args, **kwargs):
        result = func(*args, **kwargs)
        response = flask.make_response(cjson.encode(result))
        response.headers["Content-Type"] = "application/json"
        return response
    return new_func
