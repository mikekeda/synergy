import os
import requests
import urllib.parse

SITE_ENV_PREFIX = "SYNERGY"


def get_env_var(name: str, default: str = "") -> str:
    """Get all sensitive data from google vm custom metadata."""
    try:
        name = "_".join([SITE_ENV_PREFIX, name])
        res = os.environ.get(name)
        if res is not None:
            # Check env variable (Jenkins build).
            return res
        else:
            res = requests.get(
                "http://metadata.google.internal/computeMetadata/"
                "v1/instance/attributes/{}".format(name),
                headers={"Metadata-Flavor": "Google"},
            )
            if res.status_code == 200:
                return res.text
    except requests.exceptions.ConnectionError:
        return default
    return default


default_page = 1
default_items_per_page = 15

redis_cache_config = {
    "default": {
        "cache": "aiocache.RedisCache",
        "endpoint": "localhost",
        "db": 7,
        "timeout": 2,
        "serializer": {"class": "aiocache.serializers.PickleSerializer"},
    }
}

SANIC_CONFIG = {
    "DEBUG": bool(get_env_var("DEBUG", "True")),
    "SOCKET_FILE": get_env_var("SOCKET_FILE", "/temp/synergy.sock"),
    "SECRET_KEY": get_env_var("SECRET_KEY", "test secret"),
    "DB_URL": (
        "postgresql+asyncpg://"
        f"{get_env_var('DB_USER', 'user_admin')}"
        f":{urllib.parse.quote_plus(get_env_var('DB_PASSWORD', 'user_admin_pasS64!'))}"
        f"@{get_env_var('DB_HOST', '127.0.0.1')}"
        f"/{get_env_var('DB_NAME', 'users')}"
    ),
    "redis": "redis://127.0.0.1/7",
}
