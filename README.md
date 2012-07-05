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
3. Make sure you have `tmux` installed on your system. You'll need it for development/debugging.
4. Chdir into the directory, and run your first instance: `fab debug`. This will bring up *tmux* with several panes, one for each running service.
5. Open your browser and point it to *http://127.0.0.1:8080*, and voilla!

Checklist for Starting an App
=============================

1. Change your app name in `flask_app/config.py -> AUTOCLAVE_APP_NAME`.

Deploying to a Server
=====================

> *NOTE*: The automated deployment assumes there are no other critical services running on the server

To deploy your app, just run `fab deploy`:

   fab deploy -H your_host -u root -p yourpassword

