from functools import wraps

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.urls import reverse

from .models import OAuthUserSession

login_required = login_required


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
