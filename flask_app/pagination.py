import functools

from flask import jsonify
from .request_utils import dictify_model

def paged_view(func):
    @functools.wraps(func)
    def new_func(*args, **kwargs):
        returned = func(*args, **kwargs)
        return jsonify({
            "metadata": {
                "total_num_pages": 1,
                "page": 1,
            },
            "result": [dictify_model(obj) for obj in returned],
        })
    return new_func

