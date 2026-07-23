"""Settings de prueba con PostgreSQL (concurrencia real)."""
from config.settings import *  # noqa: F401, F403

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('TEST_DB_NAME', default=config('DB_NAME')),
        'USER': config('TEST_DB_USER', default=config('DB_USER')),
        'PASSWORD': config('TEST_DB_PASSWORD', default=config('DB_PASSWORD')),
        'HOST': config('TEST_DB_HOST', default=config('DB_HOST', default='localhost')),
        'PORT': config('TEST_DB_PORT', default=config('DB_PORT', default='5432')),
        'TEST': {
            'NAME': config('TEST_DB_NAME', default='motoshop_test'),
        },
    }
}

MOTOSHOP_IVA_RATE = __import__('decimal').Decimal('0.15')
