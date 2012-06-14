import flask

def render_template(template, **kwargs):
    return flask.render_template(template, request=flask.request, **kwargs)
