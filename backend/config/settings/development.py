from .base import *

DEBUG = True

# Development-specific overrides can go here
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

