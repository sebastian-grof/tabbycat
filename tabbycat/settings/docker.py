# ==============================================================================
# Docker
# ==============================================================================

import os

ALLOWED_HOSTS = ["*"]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'tabbycat',
        'USER': 'tabbycat',
        'PASSWORD': 'tabbycat',
        'HOST': 'db',
        'PORT': 5432, # Non-standard to prevent collisions,
    }
}

if bool(int(os.environ['DOCKER_REDIS'])) if 'DOCKER_REDIS' in os.environ else False:
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": "redis://redis:6379/1",
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
                "SOCKET_CONNECT_TIMEOUT": 5,
                "SOCKET_TIMEOUT": 60,
            },
        },
    }

    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels_redis.core.RedisChannelLayer",
            "CONFIG": {
                "hosts": [("redis", 6379)],
                "group_expiry": 10800,
            },
        },
    }

# ==============================================================================
# Production overrides (set via environment, e.g. on Dokploy)
# ==============================================================================

import dj_database_url  # noqa: E402

# Override the public placeholder SECRET_KEY shipped in core.py
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', SECRET_KEY)

if os.environ.get('ALLOWED_HOSTS'):
    ALLOWED_HOSTS = os.environ['ALLOWED_HOSTS'].split(',')

if os.environ.get('DATABASE_URL'):
    DATABASES['default'] = dj_database_url.parse(os.environ['DATABASE_URL'], conn_max_age=600)

if os.environ.get('REDIS_URL'):
    _redis_url = os.environ['REDIS_URL'].rstrip('/')
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": _redis_url + "/1",  # db 1; channel layer uses db 0
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
                "SOCKET_CONNECT_TIMEOUT": 5,
                "SOCKET_TIMEOUT": 60,
            },
        },
    }
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels_redis.core.RedisChannelLayer",
            "CONFIG": {"hosts": [_redis_url], "group_expiry": 10800},
        },
    }

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
if os.environ.get('CSRF_TRUSTED_ORIGINS'):
    CSRF_TRUSTED_ORIGINS = os.environ['CSRF_TRUSTED_ORIGINS'].split(',')

if os.environ.get('EMAIL_HOST'):
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = os.environ['EMAIL_HOST']
    EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
    EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'true').lower() == 'true'
    EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
    EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
    DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', EMAIL_HOST_USER)
    SERVER_EMAIL = DEFAULT_FROM_EMAIL

if os.environ.get('TAB_DIRECTOR_EMAIL'):
    TAB_DIRECTOR_EMAIL = os.environ['TAB_DIRECTOR_EMAIL']
