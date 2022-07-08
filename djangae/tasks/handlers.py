import logging
import pickle

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from .decorators import task_only
from . import environment

logger = logging.getLogger(__name__)


@csrf_exempt
@task_only
def deferred_handler(request):
    from .deferred import PermanentTaskFailure, SingularTaskFailure

    callback, args, kwargs = pickle.loads(request.body)

    logger.debug(f"[DEFERRED] Retry {environment.task_execution_count()} of deferred task")

    try:
        callback(*args, **kwargs)
    except SingularTaskFailure:
        logger.debug("Failure executing task, task retry forced")
        return HttpResponse(status=408)
    except PermanentTaskFailure:
        logger.exception("Permanent failure attempting to execute task")

    return HttpResponse("OK")
