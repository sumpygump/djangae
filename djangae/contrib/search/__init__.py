from django.conf import settings
from django.utils.module_loading import autodiscover_modules

default_app_config = 'djangae.contrib.search.apps.SearchConfig'

DJANGAE_SEARCH_QUEUE_SETTING = "DJANGAE_SEARCH_QUEUE"
_SEARCH_QUEUE = getattr(settings, DJANGAE_SEARCH_QUEUE_SETTING, "default")


def autodiscover():
    # This will find all the search.py modules and add them to model_document._registry
    # The act of importing them will call any register(model, document) statements
    # in that file.
    from djangae.contrib.search import model_document
    autodiscover_modules('search', register_to=model_document)
