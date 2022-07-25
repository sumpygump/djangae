import logging
import json
from dataclasses import asdict

from google.api_core import exceptions

from .utils import MissingSecretError, strip_keys_not_in_dataclass


class GSMBackend:
    """Secret storage backend for Google Secret Manager

    https://cloud.google.com/secret-manager

    Secrets value can either be pre-created with the gcloud cli or a default
    value will be created on first access.

        > gcloud secrets create secret-id --data-file secrets.json

    All values are stored as a single JSON object in a single secret, eg:

        {
            "secret_key": "lak123j1bn2klj31l2kjk@#KLj12kj/",
            "foo_api_key": "foo",
            "bar_api_key": "bar"
        }

    Usage:
        # settings.py

        from djangae.contrib import secrets

        MY_SECRETS = secrets.get(
            backend=secrets.GSMBackend(
                project_id="my-gcp-project-id",
                secret_id="app-secret-name"
            )
        )
        SECRET_KEY = MY_SECRETS.secret_key
    """

    def __init__(self, project_id=None, secret_id="app", version_id="latest"):
        self.project_id = project_id
        self.secret_id = secret_id
        self.version_id = version_id
        self._api_client = None

    def get_api_client(self):
        from google.cloud import secretmanager  # noqa

        if self._api_client is None:
            self._api_client = secretmanager.SecretManagerServiceClient()
        return self._api_client

    def get(self, secrets_class, create_if_missing):
        client = self.get_api_client()
        secrets = None
        name = f"projects/{self.project_id}/secrets/{self.secret_id}/versions/{self.version_id}"

        try:
            response = client.access_secret_version(request={"name": name})
            data_dict = json.loads(response.payload.data.decode("UTF-8"))
            data_dict = strip_keys_not_in_dataclass(data_dict, secrets_class)
            secrets = secrets_class(**data_dict)
        except exceptions.NotFound:
            pass
        except exceptions.PermissionDenied:
            logging.error(
                "Failed to fetch secret. Ensure the App Engine default service "
                "account has the role role roles/secretmanager.secretAccessor "
                "on the secret."
            )
            raise

        if secrets is None:
            if not create_if_missing:
                raise MissingSecretError()

            logging.warning("No secret found at %s creating", name)
            # Create a new secret
            try:
                response = client.create_secret(
                    request={
                        "parent": f"projects/{self.project_id}",
                        "secret_id": self.secret_id,
                        "secret": {"replication": {"automatic": {}}},
                    }
                )
            except exceptions.AlreadyExists:
                pass
            except exceptions.PermissionDenied:
                logging.error(
                    "Failed to create new secret. Ensure the App Engine default "
                    "service account has the role roles/secretmanager.admin"
                )
                raise

            # Create a version of the new secret
            secrets = secrets_class()
            payload = json.dumps(
                asdict(secrets),
                ensure_ascii=False,
                indent=4,
            ).encode("UTF-8")
            response = client.add_secret_version(
                request={
                    "parent": client.secret_path(self.project_id, self.secret_id),
                    "payload": {"data": payload},
                }
            )

        return secrets
