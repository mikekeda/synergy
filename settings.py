import os
import requests

SITE_ENV_PREFIX = 'SYNERGY'


def get_env_var(name, default=''):
    """ Get all sensitive data from google vm custom metadata. """
    try:
        name = '_'.join([SITE_ENV_PREFIX, name])
        res = os.environ.get(name)
        if res is not None:
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

redis_cache_config = {
    'default': {
        'cache': 'aiocache.RedisCache',
        'endpoint': 'localhost',
        'db': 7,
        'timeout': 2,
        'serializer': {
            'class': 'aiocache.serializers.PickleSerializer'
        }
    }
}
