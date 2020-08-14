from djangae.test import TestCase
from django.contrib.auth import get_user_model


User = get_user_model()


class IAPAuthenticationTests(TestCase):
    def test_user_created_if_authenticated(self):
        headers = {
            'HTTP_X_GOOG_AUTHENTICATED_USER_ID': '99999',
            'HTTP_X_GOOG_AUTHENTICATED_USER_EMAIL': 'test@example.com'
        }

        self.client.get("/", **headers)

        self.assertTrue(User.objects.exists())

        user = User.objects.get()

        self.assertEqual(user.google_iap_id, 99999)
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.username, 'test')

    def test_email_change(self):
        headers = {
            'HTTP_X_GOOG_AUTHENTICATED_USER_ID': '99999',
            'HTTP_X_GOOG_AUTHENTICATED_USER_EMAIL': 'test@example.com'
        }

        self.client.get("/", **headers)

        self.assertTrue(User.objects.exists())

        user = User.objects.get()

        self.assertEqual(user.google_iap_id, 99999)
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.username, 'test')

        headers = {
            'HTTP_X_GOOG_AUTHENTICATED_USER_ID': '99999',
            'HTTP_X_GOOG_AUTHENTICATED_USER_EMAIL': 'test22@example.com'
        }

        self.client.get("/", **headers)

        user = User.objects.get()

        self.assertEqual(user.google_iap_id, 99999)
        self.assertEqual(user.email, 'test22@example.com')

        # Username not updated
        self.assertEqual(user.username, 'test')
