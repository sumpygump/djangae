from djangae.test import TestCase
from djangae.contrib import secrets

from django.db import models, connection


class SecretModel(models.Model):
    id = models.CharField(max_length=64, primary_key=True)
    secret_key = models.CharField(max_length=50)

    class Meta:
        app_label = "djangae"


class DatastoreBackendTests(TestCase):
    def test_setting_and_retrieving_items(self):

        SecretModel.objects.create(
            id="test",
            secret_key="this is a secret"
        )

        MySecrets = secrets.get(
            backend=secrets.DatastoreBackend(
                kind_name=SecretModel._meta.db_table,
                key_name="test",
                namespace=connection.settings_dict["NAMESPACE"],
                project_id=connection.settings_dict["PROJECT"]
            ),
            create_if_missing=False
        )

        self.assertEqual(MySecrets.secret_key, "this is a secret")
