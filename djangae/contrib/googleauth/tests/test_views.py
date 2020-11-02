import json
from unittest import mock
from unittest.mock import (
    create_autospec,
    patch,
    Mock,
)

from django.contrib import auth
from django.test.utils import override_settings
from django.urls import reverse
from requests_oauthlib import OAuth2Session

from djangae.contrib.googleauth import (
    _DEFAULT_SCOPES_SETTING,
    _SCOPE_SESSION_KEY,
)
from djangae.contrib.googleauth.views import STATE_SESSION_KEY
from djangae.settings_base import ALLOWED_HOSTS
from djangae.test import TestCase

host = "test.appspot.com"
state_str = "state"
authorization_url = "http://authorization_url.com"




@override_settings(ROOT_URLCONF="djangae.contrib.googleauth.urls", ALLOWED_HOSTS=[host])
class LoginViewTestCase(TestCase):
    """Tests for djangae.contrib.backup.views"""

    def setUp(self):
        super().setUp()
        self.next_url = "go/here"
        self.client.defaults["HTTP_HOST"] = host
        self.login_url = "{}?next={}".format(reverse("googleauth_oauth2login"), self.next_url)

        # Patch oauth session
        self.oAuthSessionMock = create_autospec(OAuth2Session)
        self.oAuthSessionMock.authorization_url.return_value = (authorization_url, state_str,)
        self.oAuthSessionMock.new_state.return_value = state_str
        patcher = patch(
            'djangae.contrib.googleauth.views.OAuth2Session',
            Mock(return_value=self.oAuthSessionMock)
        )
        self.OAuthSessionMock = patcher.start()

    def tearDown(self):
        super().tearDown()
        self.OAuthSessionMock.stop()

    def test_store_next_url_in_session(self, ):
        """Tests it persists next in the session"""

        self.client.get(self.login_url)
        self.assertEqual(self.client.session[auth.REDIRECT_FIELD_NAME], self.next_url)

    @override_settings(GOOGLEAUTH_CLIENT_ID="clientid", )
    def test_create_a_oauth_session(self, ):
        """Tests it creates a oauth session"""
        self.client.get(self.login_url)

        self.OAuthSessionMock.assert_called_once()
        client_id = self.OAuthSessionMock.call_args[0][0]
        self.assertEqual(client_id, "clientid")

    def test_create_a_oauth_session_with_oauth_scopes(self, ):
        """Tests it creates a oauth session with required scopes"""

        self.client.get(self.login_url)

        self.OAuthSessionMock.assert_called_once()
        scope = self.OAuthSessionMock.call_args[1]["scope"]
        self.assertEqual(set(scope), {"openid", "profile", "email",})

    @override_settings(GOOGLEAUTH_OAUTH_SCOPES=["email", "somethingelse"])
    def test_create_a_oauth_session_with_settings_scopes(self, ):
        """Tests it creates a oauth session with provided scopes"""

        self.client.get(self.login_url)

        self.OAuthSessionMock.assert_called_once()
        scope = self.OAuthSessionMock.call_args[1]["scope"]
        self.assertEqual(set(scope), {"email", "somethingelse"})

    def test_create_a_oauth_session_with_additional_scopes(self, ):
        """Tests it creates a oauth session with addtional scopes"""
        session = self.client.session
        session[_SCOPE_SESSION_KEY] = (["additional"], False)
        session.save()

        self.client.get(self.login_url)

        self.OAuthSessionMock.assert_called_once()
        scope = self.OAuthSessionMock.call_args[1]["scope"]
        self.assertEqual(set(scope), {"openid", "profile", "email", "additional"})

    @override_settings(OAUTH2_REDIRECT_URL="http://redirect.appspot.com", )
    def test_create_a_oauth_session_with_oauth_redirect_provided(self, ):
        """Tests it creates a oauth session with the redirect provided in settings"""
        self.client.get(self.login_url)

        self.OAuthSessionMock.assert_called_once()
        redirect = self.OAuthSessionMock.call_args[1]["redirect_uri"]
        self.assertEqual(redirect, f"http://redirect.appspot.com{reverse('googleauth_oauth2callback')}")

    def test_create_a_oauth_session_with_oauth_redirect(self, ):
        """Tests it creates a oauth session with the redirect using application host"""
        self.client.get(self.login_url)

        self.OAuthSessionMock.assert_called_once()
        redirect = self.OAuthSessionMock.call_args[1]["redirect_uri"]
        self.assertIn(host, redirect)

    def test_stores_state_in_session(self, ):
        """Tests it stores auth state in session"""
        self.client.get(self.login_url)
        self.assertEqual(self.client.session[STATE_SESSION_KEY], state_str)

    @patch('djangae.contrib.googleauth.views.environment.gae_version', return_value=1)
    def test_stores_version_in_state(self, mock_gae_version, ):
        """Tests it stores auth state in session"""
        self.client.get(self.login_url)

        mock_gae_version.assert_called_once()
        self.oAuthSessionMock.authorization_url.assert_called_once()
        state = json.loads(self.oAuthSessionMock.authorization_url.call_args[1]['state'])
        self.assertEqual(state['version'], 1)

    def test_redirects_to_auth_url(self, ):
        """Tests it redirects the user to oauth url"""

        response = self.client.get(self.login_url)
        self.assertRedirects(response, authorization_url, fetch_redirect_response=False)


