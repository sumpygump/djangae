from django.db import (
    connections,
    router,
)


def _find_atomic_decorator(model):
    connection = connections[router.db_for_read(model)]

    # FIXME: When Django GCloud Connectors gets rid of its own atomic decorator
    # the Django atomic() decorator can be used regardless
    if connection.settings_dict['ENGINE'] == 'gcloudc.db.backends.datastore':
        from gcloudc.db.transaction import atomic
    else:
        from django.db.transaction import atomic

    return atomic
