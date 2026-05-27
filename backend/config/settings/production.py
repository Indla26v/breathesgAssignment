import dj_database_url
from .base import *

DEBUG = False

# Production-only overrides
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '*').split(',')

db_from_env = dj_database_url.config(conn_max_age=600, ssl_require=False)
if db_from_env:
    DATABASES['default'] = db_from_env

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY')

# CORS
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = os.environ.get('CORS_ALLOWED_ORIGINS', 'http://localhost:5173').split(',')
CORS_ALLOW_CREDENTIALS = True
