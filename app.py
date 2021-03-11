from collections import namedtuple

from aiocache import caches
import aioredis
from gino import Gino
from sanic import Sanic
from sanic.log import logger
from sanic.request import Request
from sanic.response import HTTPResponse
from sanic_jinja2 import SanicJinja2
from sanic_session import Session, AIORedisSessionInterface
from sqlalchemy.engine.url import URL

from template_tags import update_param
from settings import redis_cache_config, SANIC_CONFIG

app = Sanic(__name__)
app.config.update(SANIC_CONFIG)
app.static("/static", "./static")

db = Gino()

# Set jinja_env and session_interface to None to avoid code style warning.
app.jinja_env = namedtuple("JinjaEnv", ["globals"])({})

jinja = SanicJinja2(app, autoescape=True, enable_async=True)
app.jinja_env.globals.update(update_param=update_param)

session = Session()


@app.listener("before_server_start")
async def before_server_start(_app, loop):
    """ Initialize database connection and Redis cache. """
    if _app.config.get("DB_DSN"):
        dsn = _app.config.DB_DSN
    else:
        dsn = URL(
            drivername=_app.config.setdefault("DB_DRIVER", "asyncpg"),
            host=_app.config.setdefault("DB_HOST", "localhost"),
            port=_app.config.setdefault("DB_PORT", 5432),
            username=_app.config.setdefault("DB_USER", "postgres"),
            password=_app.config.setdefault("DB_PASSWORD", ""),
            database=_app.config.setdefault("DB_DATABASE", "postgres"),
        )

    await db.set_bind(
        dsn,
        echo=_app.config.setdefault("DB_ECHO", False),
        min_size=_app.config.setdefault("DB_POOL_MIN_SIZE", 5),
        max_size=_app.config.setdefault("DB_POOL_MAX_SIZE", 10),
        ssl=_app.config.setdefault("DB_SSL"),
        loop=loop,
        **_app.config.setdefault("DB_KWARGS", dict()),
    )

    caches.set_config(redis_cache_config)
    _app.redis = await aioredis.create_redis_pool(_app.config["redis"])
    # init extensions fabrics
    session.init_app(
        _app,
        interface=AIORedisSessionInterface(
            _app.redis,
            samesite="Strict",
            cookie_name="session" if _app.config["DEBUG"] else "__Host-session",
        ),
    )


@app.listener("after_server_stop")
async def after_server_stop(_app, __):
    """ Close all db connection on server stop. """
    await db.pop_bind().close()
    _app.redis.close()
    await _app.redis.wait_closed()


@app.middleware("request")
async def on_request(request: Request):
    request.ctx.connection = await db.acquire(lazy=True)


@app.middleware("response")
async def on_response(request: Request, _):
    conn = getattr(request.ctx, "connection", None)
    if conn is not None:
        await conn.release()


@app.exception(Exception)
async def exception_handler(
    request: Request, exception: Exception, **__
) -> HTTPResponse:
    """Exception handler returns error in json format."""
    status_code = getattr(exception, "status_code", 500)

    if status_code == 500:
        logger.exception(exception)

    return jinja.render(
        "error.html",
        request,
        status=status_code,
        status_code=status_code,
        message=" ".join(str(arg) for arg in exception.args),
    )
