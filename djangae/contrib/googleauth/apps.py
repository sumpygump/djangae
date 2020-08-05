from django.apps import AppConfig
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from . import (
    _CLIENT_ID_SETTING,
    _CLIENT_SECRET_SETTING,
)


class GoogleauthConfig(AppConfig):
    name = 'djangae.contrib.googleauth'
    verbose_name = "Googleauth"

    def ready(self):
        oauth_backend = 'djangae.contrib.googleauth.backends.oauth2.OAuthBackend'
        auth_backends = getattr(settings, "AUTHENTICATION_BACKENDS", [])
        if oauth_backend in auth_backends:
            client_id = getattr(settings, _CLIENT_ID_SETTING, None)
            secret = getattr(settings, _CLIENT_SECRET_SETTING, None)

            if not client_id or not secret:
                raise ImproperlyConfigured(
                    "You must specify a %s and %s in settings" % (
                        _CLIENT_ID_SETTING, _CLIENT_SECRET_SETTING
                    )
                )
