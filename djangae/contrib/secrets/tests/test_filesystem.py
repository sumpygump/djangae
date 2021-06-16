import json

from djangae.test import TestCase
from djangae.contrib import secrets


class FilesystemBackendTests(TestCase):
    def test_setting_and_retrieving_items(self):
        filename = "/tmp/filesystem.secrets"

        with open(filename, "w") as f:
            f.write(json.dumps({
                "secret_key": "apples"
            }))

        MySecrets = secrets.get(
            backend=secrets.FilesystemBackend(filename=filename),
            create_if_missing=False
        )

        self.assertEqual(MySecrets.secret_key, "apples")
