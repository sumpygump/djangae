from djangae.test import TestCase
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.test import override_settings, LiveServerTestCase
from django.shortcuts import reverse
from django.urls import (
    include,
    path,
)



class PermissionTests(TestCase):
    pass


@login_required(login_url='/googleauth/oauth2/login/')
def a_protected_view(request):
    return HttpResponse("OK")


urlpatterns = [
    path("protected", a_protected_view),
    path("googleauth/", include("djangae.contrib.googleauth.urls"))
]


@override_settings(ROOT_URLCONF=__name__)
class OAuthTests(LiveServerTestCase):

    def test_redirect_to_authorization_url(self):
        """
            Access to a page that is login_required
            should redirect to the authorization url
        """
        live_server_domain = self.live_server_url.split('://')[-1]
        response = self.client.get('/protected', HTTP_HOST=live_server_domain)
        self.assertTrue(reverse("googleauth_oauth2login") in response.url)
        self.assertEqual(302, response.status_code)

        response = self.client.get(response.url, HTTP_HOST=live_server_domain)
        self.assertTrue('https://accounts.google.com/o/oauth2/v2/auth' in response.url)
        self.assertEqual(302, response.status_code)

    def test_oauth_callback_creates_session(self):
        """
            Should create an oauth session (if valid)
            and then redirect to the correct URL.

            Middleware should take care of authenticating the
            Django session
        """
        pass

    def test_login_checks_scope_whitelist(self):
        """
            Accessing the oauth login page with
            additional scopes in the GET param
            should only work for whitelisted scopes
        """
        pass

    def test_login_respects_additional_scopes(self):
        """
            Accessing the oauth login page with additional
            scopes in the GET param should forward those
            to the authorization url
        """
        pass


class OAuth2CallbackTests(TestCase):

    def test_invalid_token_raises_404(self):
        pass

    def test_scopes_must_be_whitelisted(self):
        pass

    def test_callback_sets_session_key(self):
        pass


class OAuthScopesRequiredTests(TestCase):
    def test_oauth_scopes_required_redirects_to_login(self):
        pass

    def test_oauth_scopes_required_redirects_for_additional_scopes(self):
        pass


class AuthBackendTests(TestCase):
    def test_valid_oauth_session_creates_django_session(self):
        pass

    def test_invalid_oauth_session_logs_out_django(self):
        pass

    def test_backend_does_nothing_if_authed_with_different_backend(self):
        """
            If you have the model backend and oauth backend (for example)
            then we don't log someone out if they authed with the model
            backend
        """
        pass
