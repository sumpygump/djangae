import threading

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from google.cloud import logging
from google.cloud.logging_v2.handlers.handlers import CloudLoggingHandler

_client = None
_client_lock = threading.Lock()

_LOGGING_MIDDLEWARE_NAME = "google.cloud.logging_v2.handlers.middleware.request.RequestMiddleware"


class DjangaeLoggingHandler(CloudLoggingHandler):
    """
        This configures the Cloud Logging client.
    """

    def __init__(self, *args, **kwargs):
        global _client

        if _LOGGING_MIDDLEWARE_NAME not in settings.MIDDLEWARE:
            raise ImproperlyConfigured(
                "You must install the %s middleware to use the LoggingHandler" % _LOGGING_MIDDLEWARE_NAME
            )

        # We use a double-checked lock here to avoid the potential race condition between
        # checking to see if the client was initialised, and it actually being
        # initialized.
        if not _client:
            with _client_lock:
                if not _client:
                    _client = logging.Client()
                    _client.setup_logging()

        kwargs.setdefault("client", _client)
        super().__init__(*args, **kwargs)
