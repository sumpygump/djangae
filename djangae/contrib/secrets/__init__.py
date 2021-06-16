from .datastore import DatastoreBackend
from .filesystem import FilesystemBackend  # noqa
from .gsm import GSMBackend  # noqa
from .default import DefaultSecrets # noqa


def get(secrets_class=DefaultSecrets, backend=None, create_if_missing=True):
    if backend is None:
        backend = DatastoreBackend()

    return backend.get(secrets_class, create_if_missing)
