import logging
from importlib import import_module

from django.conf import settings
from django.http import HttpResponse

from djangae.tasks import decorators
from djangae.core.signals import module_started, module_stopped


logger = logging.getLogger(__name__)


@decorators.internal_only
def warmup(request):
    """
        Provides default procedure for handling warmup requests on App
        Engine. Just add this view to your main urls.py.
    """
    for app in settings.INSTALLED_APPS:
        for name in ('urls', 'views', 'models'):
            try:
                import_module('%s.%s' % (app, name))
            except ImportError:
                pass
    return HttpResponse("OK")


@decorators.internal_only
def start(request):
    module_started.send(sender=__name__, request=request)
    return HttpResponse("OK")


@decorators.internal_only
def stop(request):
    module_stopped.send(sender=__name__, request=request)
    return HttpResponse("OK")


@decorators.task_only
def clearsessions(request):
    engine = import_module(settings.SESSION_ENGINE)
    try:
        engine.SessionStore.clear_expired()
    except NotImplementedError:
        logger.exception(
            "Session engine '%s' doesn't support clearing "
            "expired sessions.\n", settings.SESSION_ENGINE
        )
    return HttpResponse("OK")
