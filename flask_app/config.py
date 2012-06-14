import os
SECRET_KEY = "4042e86014be1712ee47c522e6e374f4a63da171096c7d2b5719be33a3e85aea6dab5e297440efda030cd83e90845d1a2e2e4e3324911eadcd7c3af970d6e660"

# ports
AUTOCLAVE_APP_TCP_PORT                 = 8000
AUTOCLAVE_DATABASE_HOST                = "127.0.0.1"
AUTOCLAVE_DEPLOYMENT_FRONTEND_TCP_PORT = 80
AUTOCLAVE_STATIC_ROOT                  = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "static"))
AUTOCLAVE_TESTING_FRONTEND_TCP_PORT    = 8080

