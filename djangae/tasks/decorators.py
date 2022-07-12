
from functools import wraps

from django.http import HttpResponseForbidden

from djangae.utils import get_client_ip
from .environment import is_in_task, is_in_cron


def task_only(view_function):
    """ View decorator for restricting access to tasks (and crons) of the application
        only.
    """

    @wraps(view_function)
    def replacement(request, *args, **kwargs):
        if not any((is_in_task(), is_in_cron())):
            return HttpResponseForbidden("Access denied.")

        return view_function(request, *args, **kwargs)

    return replacement


def task_or_superuser_only(view_function):
    @wraps(view_function)
    def replacement(request, *args, **kwargs):
        is_superuser = (
            getattr(request, "user", None) and
            request.user.is_authenticated and
            request.user.is_superuser
        )

        if not any((is_superuser, is_in_task(), is_in_cron())):
            return HttpResponseForbidden("Access denied.")

        return view_function(request, *args, **kwargs)

    return replacement


def csrf_exempt_if_task(view_function):
    class Replacement(object):
        def __call__(self, request, *args, **kwargs):
            return view_function(request, *args, **kwargs)

        @property
        def csrf_exempt(self):
            return any((is_in_task(), is_in_cron()))

    return Replacement()


def internal_only(view_function):
    """ View decorator for restricting access to internal 0.1.0.* ip addresses only.
        This decorator is particularly useful for requests related to automatically scaling,
        i.e., /_ah/warmup|start|stop.
        https://cloud.google.com/appengine/docs/standard/python3/understanding-firewalls
    """

    @wraps(view_function)
    def replacement(request, *args, **kwargs):
        request_ip = get_client_ip(request)
        if not request_ip or not request_ip.startswith('0.1.0.'):
            return HttpResponseForbidden("Access denied.")

        return view_function(request, *args, **kwargs)

    return replacement
