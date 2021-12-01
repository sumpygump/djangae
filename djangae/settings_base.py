from djangae.environment import is_production_environment
from djangae.tasks.environment import tasks_location
from django.utils.log import DEFAULT_LOGGING

FILE_CACHE_LOCATION = '/tmp/cache' if is_production_environment() else '.cache'

CACHES = {
    # We default to the filesystem cache, since it's quick and easy for simple app
    # For larger application you should consider Cloud Memory Store (which does not have a free tier)
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': FILE_CACHE_LOCATION,
    }
}

LOGGING = DEFAULT_LOGGING.copy()
LOGGING['loggers']['djangae'] = {'level': 'WARN'}

# If on a production service, enable the StackDriver logging so that
# request logs are correctly grouped.
if is_production_environment():
    from google.cloud import logging
    client = logging.Client()

    LOGGING['handlers']['console']['class'] = 'google.cloud.logging_v2.handlers.CloudLoggingHandler'
    LOGGING['handlers']['console']['client'] = client
    LOGGING['handlers']['django.server']['class'] = 'google.cloud.logging_v2.handlers.CloudLoggingHandler'
    LOGGING['handlers']['django.server']['client'] = client


# Setting to * is OK, because GAE takes care of domain routing - setting it to anything
# else just causes unnecessary pain when something isn't accessible under a custom domain
ALLOWED_HOSTS = ("*",)


# We set this default because Cloud Datastore uses signed 64 bit integers for IDs
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# Set a default CLOUD_TASKS_LOCATION variable based on the environment (if we can)
CLOUD_TASKS_LOCATION = tasks_location()
