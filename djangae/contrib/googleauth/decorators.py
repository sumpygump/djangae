import functools

from django.http import HttpResponseRedirect
from django.urls import (
    reverse,
)


def oauth_scopes_required(function, scopes):
    @functools.wraps(function)
    def wrapper(request, *args, **kwargs):
        login_reverse = f"{reverse('googleauth_oauth2login')}?next={request.get_full_path()}"
        if request.user.is_authenticated and hasattr(request.user, 'oauthusersession'):
            additional_scopes = set(scopes)
            current_scopes = set(request.user.oauthusersession.scopes)
            if additional_scopes - current_scopes != set():
                # scopes have been added, we should redirect to login flow with those scopes
                serialized_scopes = ",".join(additional_scopes)
                login_reverse = f"{login_reverse}&scopes={serialized_scopes}"
                return HttpResponseRedirect(login_reverse)
            return function(request, *args, **kwargs)
        else:
            if scopes:
                serialized_scopes = ",".join(scopes)
                login_reverse = f"{login_reverse}&scopes={serialized_scopes}"
            return HttpResponseRedirect(login_reverse)

    return wrapper
