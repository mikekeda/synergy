import os
import requests

SITE_ENV_PREFIX = 'SYNERGY'


def get_env_var(name, default=''):
    """Get all sensitive data from google vm custom metadata."""
    try:
        name = '_'.join([SITE_ENV_PREFIX, name])
        res = os.environ.get(name)
        if res:
            # Check env variable (Jenkins build).
            return res
        else:
            res = requests.get(
                'http://metadata.google.internal/computeMetadata/'
                'v1/instance/attributes/{}'.format(name),
                headers={'Metadata-Flavor': 'Google'}
            )
            if res.status_code == 200:
                return res.text
    except requests.exceptions.ConnectionError:
        return default
    return default


default_page = 1
default_items_per_page = 15

db_config = {
    'user': get_env_var('DB_USER', 'user_admin'),
    'password': get_env_var('DB_PASSWORD', 'user_admin_pasS64!'),
    'host': get_env_var('DB_HOST', '127.0.0.1'),
    'database': get_env_var('DB_NAME', 'users')
}

redis_cache_config = {
    'default': {
        'cache': 'aiocache.RedisCache',
        'endpoint': 'localhost',
        'db': 4,
        'timeout': 2,
        'serializer': {
            'class': 'aiocache.serializers.PickleSerializer'
        }
    }
}

redis_session_config = {
    'host': 'localhost',
    'port': 6379,
    'db': 4,
    'poolsize': 10
}
