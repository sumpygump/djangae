from dataclasses import asdict

from google.cloud import datastore

from .utils import (
    MissingSecretError,
    strip_keys_not_in_dataclass,
)


class DatastoreBackend:
    """Secret storage backend for Google Cloud Datastore.

    Secret values are stored as properties on a single datastore
    entity.

    Usage:
        # settings.py
        from djangae.contrib import secrets
        MY_SECRETS = secrets.get(backend=secrets.DatastoreBackend())
        SECRET_KEY = MY_SECRETS.secret_key
    """

    def __init__(self, kind_name="Secrets", key_name="secrets", namespace=None, project_id=None):
        self.kind_name = kind_name
        self.key_name = key_name
        self.namespace = namespace or ""
        self.project = project_id

    def get_datastore_client(self):
        return datastore.Client(
            namespace=self.namespace,
            project=self.project
        )

    def get(self, secrets_class, create_if_missing):
        client = self.get_datastore_client()

        with client.transaction():
            key = client.key(self.kind_name, self.key_name, namespace=self.namespace)
            entity = client.get(key)

            if create_if_missing and not entity:
                new_secrets = secrets_class()
                entity = datastore.Entity(key=key)
                entity.update(asdict(new_secrets))
                client.put(entity)
            elif not entity:
                raise MissingSecretError()

            data_dict = strip_keys_not_in_dataclass(dict(entity), secrets_class)
            return secrets_class(**data_dict)
