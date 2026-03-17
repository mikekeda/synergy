import os
import requests
import urllib.parse

SITE_ENV_PREFIX = "SYNERGY"


def get_env_var(name: str, default: str = "") -> str:
    """Get sensitive data from env vars, Oracle Cloud IMDS, or Google Cloud metadata."""
    name = f"{SITE_ENV_PREFIX}_{name}"

    env_var = os.environ.get(name)
    if env_var is not None:
        return env_var

    # Try Oracle Cloud IMDS (only reachable on OCI instances)
    try:
        res = requests.get(
            f"http://169.254.169.254/opc/v2/instance/metadata/{name}",
            headers={"Authorization": "Bearer Oracle"},
            timeout=2,
        )
        if res.status_code == 200:
            return res.text.strip()
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        pass

    # Try Google Cloud metadata (only reachable on GCP instances)
    try:
        res = requests.get(
            f"http://metadata.google.internal/computeMetadata/v1/instance/attributes/{name}",
            headers={"Metadata-Flavor": "Google"},
            timeout=2,
        )
        if res.status_code == 200:
            return res.text.strip()
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        pass

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
