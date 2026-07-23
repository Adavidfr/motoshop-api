"""Settings for automated tests (SQLite in-memory)."""
from decimal import Decimal

from config.settings import *  # noqa: F401, F403

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

MOTOSHOP_IVA_RATE = Decimal('0.12')