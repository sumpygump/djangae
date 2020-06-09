from djangae.environment import application_id
from django.core.exceptions import ImproperlyConfigured
from google_auth_oauthlib.flow import Flow
import google.auth

from .models import AppOAuthCredentials


def create_oauth2_flow(scopes):
    credentials, project = google.auth.default()

    if (not credentials.client_id) or (not credentials.client_secret):
        raise ImproperlyConfigured(
            "No OAuth credentials have been set for application: %s" % (
                application_id()
            )
        )

    flow = Flow(
        client_id=credentials.client_id,
        scope=scopes,
    )

    return flow
