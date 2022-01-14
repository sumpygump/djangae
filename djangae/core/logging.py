import threading

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from google.cloud import logging
from google.cloud.logging_v2.handlers._helpers import (
    _DJANGO_TRACE_HEADER,
    _parse_trace_span,
)
from google.cloud.logging_v2.handlers.app_engine import (
    _TRACE_ID_LABEL,
    AppEngineHandler,
)

from djangae.contrib.common import get_request


_client = None
_client_lock = threading.Lock()

_DJANGAE_MIDDLEWARE_NAME = "djangae.contrib.common.middleware.RequestStorageMiddleware"


class DjangaeLoggingHandler(AppEngineHandler):
    """
        This grabs the trace_id from Djangae's request
        middleware for log grouping
    """

    def __init__(self, *args, **kwargs):
        global _client_lock
        global _client

        if _DJANGAE_MIDDLEWARE_NAME not in settings.MIDDLEWARE:
            raise ImproperlyConfigured(
                "You must install the %s middleware to use the DjangaeLoggingHandler" % _DJANGAE_MIDDLEWARE_NAME
            )

        # We use a lock here to avoid the potential race condition between
        # checking to see if the client was initialised, and it actually being
        # initialized.
        with _client_lock:
            if not _client:
                _client = logging.Client()
                _client.setup_logging()

        kwargs.setdefault("client", _client)
        super().__init__(*args, **kwargs)

    def get_gae_labels(self):
        gae_labels = {}

        trace_id, _ = self.get_trace_and_span_id_from_djangae()
        if trace_id is not None:
            gae_labels[_TRACE_ID_LABEL] = trace_id

        return gae_labels

    def get_trace_and_span_id_from_djangae(self):
        request = get_request()

        if request is None:
            return None, None

        # find trace id and span id
        header = request.META.get(_DJANGO_TRACE_HEADER)
        trace_id, span_id = _parse_trace_span(header)

        return trace_id, span_id

    def emit(self, record):
        record.trace, record.span_id = self.get_trace_and_span_id_from_djangae()
        return super().emit(record)
