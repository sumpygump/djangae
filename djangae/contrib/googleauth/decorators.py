from functools import wraps
from urllib.parse import (
    urlparse,
    urlunparse,
)

from django.conf import settings
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.http import (
    HttpResponseRedirect,
    QueryDict,
)
from django.shortcuts import resolve_url
from django.urls import reverse

from .models import OAuthUserSession


# Some methods in this file have been duplicated from django.contrib.auth.
# The reason is that if you import login_required from Django, it will then
# import redirect_to_login, this is a view, and in that views file
# there is an import from django.contrib.auth.models and usage of
# django.contrib.auth.User which breaks if you don't have django.contrib.auth
# installed in your INSTALLED_APPS.

def _redirect_to_login(next, login_url=None, redirect_field_name=REDIRECT_FIELD_NAME):
    """
    Redirect the user to the login page, passing the given 'next' page.
    """
    resolved_url = resolve_url(login_url or settings.LOGIN_URL)

    login_url_parts = list(urlparse(resolved_url))
    if redirect_field_name:
        querystring = QueryDict(login_url_parts[4], mutable=True)
        querystring[redirect_field_name] = next
        login_url_parts[4] = querystring.urlencode(safe='/')

    return HttpResponseRedirect(urlunparse(login_url_parts))


def user_passes_test(test_func, login_url=None, redirect_field_name=REDIRECT_FIELD_NAME):
    """
    Decorator for views that checks that the user passes the given test,
    redirecting to the log-in page if necessary. The test should be a callable
    that takes the user object and returns True if the user passes.
    """

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if test_func(request.user):
                return view_func(request, *args, **kwargs)
            path = request.build_absolute_uri()
            resolved_login_url = resolve_url(login_url or settings.LOGIN_URL)
            # If the login url is the same scheme and net location then just
            # use the path as the "next" url.
            login_scheme, login_netloc = urlparse(resolved_login_url)[:2]
            current_scheme, current_netloc = urlparse(path)[:2]
            if ((not login_scheme or login_scheme == current_scheme) and
                    (not login_netloc or login_netloc == current_netloc)):
                path = request.get_full_path()
            return _redirect_to_login(
                path, resolved_login_url, redirect_field_name)
        return _wrapped_view
    return decorator


def login_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url=None):
    """
    Decorator for views that checks that the user is logged in, redirecting
    to the log-in page if necessary.
    """
    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated,
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator


def oauth_scopes_required(function, scopes):
    @wraps(function)
    def wrapper(request, *args, **kwargs):
        login_reverse = f"{reverse('googleauth_oauth2login')}?next={request.get_full_path()}"

        oauth_session = (
            OAuthUserSession.objects.filter(pk=request.user.google_oauth_id).first()
            if request.user.is_authenticated
            else None
        )

        if oauth_session:
            # If we have an oauth session but we are asking for more scopes
            # then send them through the auth process again
            additional_scopes = set(scopes)
            current_scopes = set(oauth_session.scopes)

            if additional_scopes - current_scopes:
                # scopes have been added, we should redirect to login flow with those scopes
                serialized_scopes = ",".join(current_scopes.union(additional_scopes))
                login_reverse = f"{login_reverse}&scopes={serialized_scopes}"
                return HttpResponseRedirect(login_reverse)
            return function(request, *args, **kwargs)
        else:
            if scopes:
                serialized_scopes = ",".join(scopes)
                login_reverse = f"{login_reverse}&scopes={serialized_scopes}"
            return HttpResponseRedirect(login_reverse)

    return wrapper
