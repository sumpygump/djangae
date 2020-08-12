import os
from djangae.test import TestCase


class LocalIAPMiddlewareTests(TestCase):

    def test_login_view_displayed(self):
        response = self.client.get("/_dj/login/")
        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")
        self.assertTrue("id_email" in content)

    def test_redirect_on_successful_login(self):
        form_data = {
            "email": "test@example.com"
        }

        response = self.client.post("/_dj/login/?redirect=/", form_data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], "/")

    def test_login_failure(self):
        form_data = {
            "email": "test"
        }

        response = self.client.post("/_dj/login/?redirect=/", form_data)
        self.assertEqual(response.status_code, 200)

    def test_noop_on_production(self):
        try:
            os.environ['GAE_ENV'] = 'standard'
            response = self.client.get("/_dj/login/")
            self.assertEqual(404, response.status_code)
        finally:
            del os.environ['GAE_ENV']
