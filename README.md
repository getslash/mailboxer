Autoclave
=========

Autoclave is a ready-to-deploy skeleton for building in-house web-based apps. Its goal is to provide a "batteries included" approach for rapid webapp development for small/medium scale apps.

Autoclave includes:

* A fabric file that can deploy the app to your (preferably dedicated) Ubuntu-based server, as well as rapidly build a test environment on your local machine
* A backend implemented in Python using the [Flask](http://flask.pocoo.org) framework, running on top of [gevent](http://www.gevent.org/)
* A MongoDB database engine (deployed to the same server by default)
* A Redis instance (deployed to the same server by default)
* A Celery/Celerybeat worker, along with a RabbitMQ broker, to easily support background operations carried out by your app
* An *nginx* frontend proxying your app and serving static files.
* A stylesheet overlaying [Twitter Bootstrap](http://twitter.github.com/bootstrap/)
* jQuery ready to use, along with [pnotify](http://pinesframework.org/pnotify/) notifications
* A server-side utility library for rapidly implementing REST api's over HTTP with JSON encapsulation

Getting Started
===============

1. Clone the autoclave repository to your development environment. Let's say you put it in `~/autoclave`.
2. Install dependencies: `pip install -r ~/autoclave/pip_requirements`
3. To debug autoclave, you'll need `tmux`, `redis`, `mongodb`, `rabbitmq` and `nginx`.
4. Chdir into the directory, and run your first instance: `fab debug`. This will bring up *tmux* with several panes, one for each running service.
5. Open your browser and point it to *http://127.0.0.1:8080*, and voilla!

Checklist for Starting an App
=============================

1. Change your app name in `flask_app/config/app.py -> APP_NAME`.

Deploying to a Server
=====================

> *NOTE*: The automated deployment assumes there are no other critical services running on the server

To deploy your app, just run `fab deploy`:

   fab deploy -H your_host -u root -p yourpassword

What's Inside?
==============

HTML, CSS
---------

Autoclave includes the excellent Twitter Bootsrap by default. You can add and override styles by editing `static_src/style.less` and rebuilding the CSS with `fab compile_css`.

Data Storage with MongoDB
-------------------------

To get a MongoDB connection (via Pymongo):

 from .db import get_connection
 connection = get_connection()
 connection["my_db"]["my_collection"].find({"field" : "value"})

Caching, Key-Value Store and IPC with Redis
-------------------------------------------

For many use cases like distributed locking, caching etc. Redis is extremely useful. Autoclave includes Redis, and a working binding:

 from .redis import get_connection
 connection = get_connection() # a redis-py StrictRedis connection
 connection.set("key", "value")

Background Tasks with Celery
----------------------------

You can easily add background tasks to your webapp by editing `flask_app/tasks.py`. For instance, you can add:

 @celery.task
 def test_task():
     time.sleep(5)

For more information on how to fire your task, refer to the [Celery documentation](http://www.celeryproject.org/docs-and-support/).

Javascript
----------

### Notifications

Notifications can be easily achieved like so:

 autoclave.notify_info("Hey there!");

Or alternatively:

 autoclave.notify("Hello", "error");

Available notification types are "error", "warning", "info" and "success", as in [pnotify](http://pinesframework.org/pnotify/).

### API

Making your app's client-side code call into the backend via a clean API doesn't have to be a mess. Define your API as a Python function decorated with the `api_handler` decorator:

  from .api import api_handler

  @api_handler("/format_string_and_two_numbers", string=str, a=int, b=int)
  def format(string, a, b):
      return {"result" : "{}{}{}".format(string, a, b)}

And your function will be accessible for POSTing through *<API ROOT>*/format_string_and_two_numbers. (API ROOT is set with API_ROOT in the configuration file). Calling your function is done by posting a JSON dict with the arguments to the specified URL, and the returned JSON is the exact dict returned by the function. Adding code that calls this from your app's client-side Javascript is easy:

  autoclave.api.call("/api/format_string_and_two_numbers", {"string" : "hello", "a" : 2, "b", 3})
     .success(function(data) {
         autoclave.notify_success("Result is " + data.result)
     });

Also, Autoclave provides the @returns_json decorator for views that want to return simple Pythonic values to be translated into JSON automatically.
