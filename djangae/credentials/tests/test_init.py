
from djangae.credentials import default
from djangae.credentials import default, ServiceAccountCredentials
from djangae.test import TestCase
from google.auth import credentials
from google.auth.exceptions import DefaultCredentialsError
from unittest.mock import patch, Mock

class CredentialsTestCase(TestCase):

    @patch('djangae.credentials.is_production_environment', return_value=False)
    @patch('google.auth.default')
    def test_default_for_development(self, auth_default, is_production_environment_mock):
        default()
        auth_default.assert_called_once()

    @patch('djangae.credentials.is_production_environment', return_value=True)
    @patch('djangae.credentials.ServiceAccountCredentials')
    def test_default_for_prod(self, ServiceAccountCredentialsmock, is_production_environment_mock):
        default()
        ServiceAccountCredentialsmock.assert_called_once()



