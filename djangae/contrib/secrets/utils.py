from dataclasses import dataclass


class MissingSecretError(RuntimeError):
    pass


def strip_keys_not_in_dataclass(data_dict: dict, dc: dataclass) -> dict:
    """Return a copy of `data_dict` removing any keys that are not
    properties of the dataclass dc.
    """
    return {k: v for k, v in data_dict.items() if k in dc.__dataclass_fields__.keys()}
