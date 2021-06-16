import json
import logging
import os
from dataclasses import asdict

from .utils import (
    MissingSecretError,
    strip_keys_not_in_dataclass,
)


class FilesystemBackend:
    """Secrets storage backend which uses a local JSON file.

    Usage:
        # settings.py
        from djangae.contrib import secrets
        MY_SECRETS = secrets.get(
            backend=secrets.FilesystemBackend(filename=FILENAME)
        )
        SECRET_KEY = MY_SECRETS.secret_key
    """

    def __init__(self, filename):
        self.filename = filename

    def get(self, secrets_class, create_if_missing):
        if not os.path.exists(self.filename):
            if not create_if_missing:
                raise MissingSecretError()

            secrets = secrets_class()
            logging.warning("No secrets file found. Creating file at %s", self.filename)
            with open(self.filename, "w") as f:
                f.write(json.dumps(asdict(secrets)))
        else:
            logging.warning("Loading existing secret file from %s", self.filename)
            with open(self.filename, "r") as f:
                data_dict = json.loads(f.read())

            data_dict = strip_keys_not_in_dataclass(data_dict, secrets_class)
            secrets = secrets_class(**data_dict)

        return secrets
