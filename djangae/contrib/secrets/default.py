from dataclasses import dataclass, field

from django.core.management.utils import get_random_secret_key


@dataclass
class DefaultSecrets:
    secret_key: str = field(default_factory=get_random_secret_key)
