import datetime
import logging

from django.conf import settings
from django.contrib import auth
from django.http import (
    Http404,
    HttpResponseBadRequest,
    HttpResponseRedirect,
)
from django.urls import reverse
from django.utils import timezone

from oauthlib.oauth2.rfc6749.errors import MismatchingStateError
from requests_oauthlib import OAuth2Session

from . import (
    _CLIENT_ID_SETTING,
    _CLIENT_SECRET_SETTING,
)
from .models import OAuthUserSession

STATE_SESSION_KEY = 'oauth-state'
_DEFAULT_OAUTH_SCOPES = [
    "openid",
    "profile",
    "email"
]
AUTHORIZATION_BASE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://www.googleapis.com/oauth2/v4/token"

GOOGLE_USER_INFO = "https://www.googleapis.com/oauth2/v1/userinfo"

_DEFAULT_WHITELISTED_SCOPES = _DEFAULT_OAUTH_SCOPES[:]

# The time in seconds that we take away from the given
# expires_in value to account for delay from the server
# to the application. "expires_in" is relative to the time
# the token was granted, not the time we process it
_TOKEN_EXPIRATION_GUARD_TIME = 5


def _get_scopes(request_scopes):
    if not request_scopes:
        return getattr(settings, "GOOGLEAUTH_OAUTH_SCOPES", _DEFAULT_OAUTH_SCOPES)
        return _DEFAULT_WHITELISTED_SCOPES
    else:
        parsed_scopes = request_scopes.split(',')
        WHITELISTED_SCOPES = getattr(settings, "GOOGLE_OAUTH_SCOPE_WHITELIST", _DEFAULT_WHITELISTED_SCOPES)
        if set(parsed_scopes) - set(WHITELISTED_SCOPES) != set():
            raise Http404("Not all scopes were whitelisted for the application.")
        return parsed_scopes


def login(request):
    """
        This view should be set as your login_url for using OAuth
        authentication. It will trigger the main oauth flow.
    """
    original_url = f"{request.scheme}://{request.META['HTTP_HOST']}{reverse('googleauth_oauth2callback')}"
    scopes = _get_scopes(request.GET.get('scopes'))
    next_url = request.GET.get('next')

    if next_url:
        request.session[auth.REDIRECT_FIELD_NAME] = next_url

    client_id = getattr(settings, _CLIENT_ID_SETTING)
    assert client_id

    google = OAuth2Session(client_id, scope=scopes, redirect_uri=original_url)
    authorization_url, state = google.authorization_url(
        AUTHORIZATION_BASE_URL,
        access_type="offline",
        prompt="select_account"
    )
    request.session[STATE_SESSION_KEY] = state

    return HttpResponseRedirect(authorization_url)


def _calc_expires_at(expires_in):
    """
        Given an expires_in seconds time from
        the Google OAuth2 authentication process,
        this returns an actual datetime of when
        the expiration is, relative to the current time
    """

    if not expires_in:
        # Already expired
        return timezone.now()

    try:
        expires_in = int(expires_in)
    except (TypeError, ValueError):
        return timezone.now()

    expires_in -= _TOKEN_EXPIRATION_GUARD_TIME
    return timezone.now() + datetime.timedelta(seconds=expires_in)


def oauth2callback(request):
    original_url = f"{request.scheme}://{request.META['HTTP_HOST']}{reverse('googleauth_oauth2callback')}"

    if STATE_SESSION_KEY not in request.session:
        return HttpResponseBadRequest()

    client_id = getattr(settings, _CLIENT_ID_SETTING)
    client_secret = getattr(settings, _CLIENT_SECRET_SETTING)

    assert client_id and client_secret

    google = OAuth2Session(
        client_id,
        state=request.session[STATE_SESSION_KEY],
        redirect_uri=original_url
    )

    try:
        token = google.fetch_token(
            TOKEN_URL,
            client_secret=client_secret,
            authorization_response=request.build_absolute_uri()
        )
    except MismatchingStateError:
        logging.exception("Mismatched state error in oauth handling")
        return HttpResponseBadRequest()

    next_url = request.session[auth.REDIRECT_FIELD_NAME]
    if google.authorized and next_url:
        profile = google.get(GOOGLE_USER_INFO)
        pk = profile["id"]

        session, _ = OAuthUserSession.objects.update_or_create(
            pk=pk,
            defaults=dict(
                access_token=token['access_token'],
                refresh_token=token['refresh_token'],
                token_type=token['token_type'],
                expires_at=_calc_expires_at(token['expires_in']),
                profile=profile
            )
        )

        # credentials are valid, we should authenticate the user
        user = auth.authenticate(request, oauth_session=session)
        auth.login(request, user)
        return HttpResponseRedirect(next_url)

    return HttpResponseRedirect(reverse("googleauth_oauth2login"))
