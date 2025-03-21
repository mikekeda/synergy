from aiocache import caches
from redis import asyncio as aioredis
from sanic import Sanic
from sanic.log import logger
from sanic.request import Request
from sanic.response import HTTPResponse
from sanic_jinja2 import SanicJinja2
from sanic_session import Session
from sanic_session.base import BaseSessionInterface
from sqlalchemy.ext.asyncio import create_async_engine

from template_tags import update_param
from settings import redis_cache_config, SANIC_CONFIG

app = Sanic(__name__)
app.config.update(SANIC_CONFIG)
app.static("/static", "./static")

jinja = SanicJinja2(app, autoescape=True, enable_async=True)
jinja.env.globals["update_param"] = update_param

session = Session()


class RedisSessionInterface(BaseSessionInterface):
    def __init__(
        self,
        redis,
        domain: str = None,
        expiry: int = 2592000,
        httponly: bool = True,
        cookie_name: str = "session",
        prefix: str = "session:",
        sessioncookie: bool = False,
        samesite: str = None,
        session_name: str = "session",
        secure: bool = False,
    ):

        self.redis = redis

        super().__init__(
            expiry=expiry,
            prefix=prefix,
            cookie_name=cookie_name,
            domain=domain,
            httponly=httponly,
            sessioncookie=sessioncookie,
            samesite=samesite,
            session_name=session_name,
            secure=secure,
        )

    async def _get_value(self, prefix, sid):
        return await self.redis.get(self.prefix + sid)

    async def _delete_key(self, key):
        await self.redis.delete(key)

    async def _set_value(self, key, data):
        await self.redis.setex(key, self.expiry, data)


@app.listener("before_server_start")
async def before_server_start(_app, _):
    """Initialize database connection and Redis cache."""
    _app.ctx.engine = create_async_engine(SANIC_CONFIG["DB_URL"])

    caches.set_config(redis_cache_config)
    _app.ctx.redis = await aioredis.Redis.from_url(_app.config["redis"])
    # init extensions fabrics
    session.init_app(
        _app,
        interface=RedisSessionInterface(
            _app.ctx.redis,
            samesite="Strict",
            cookie_name="session" if _app.config["DEBUG"] else "__Host-session",
        ),
    )


@app.listener("after_server_stop")
async def after_server_stop(_app, __):
    """Close all db connection on server stop."""
    _app.ctx.redis.close()


@app.middleware("request")
async def on_request(request: Request):
    request.ctx.conn = await request.app.ctx.engine.connect()


@app.middleware("response")
async def on_response(request: Request, _):
    await request.ctx.conn.commit()
    await request.ctx.conn.close()


@app.exception(Exception)
async def exception_handler(
    request: Request, exception: Exception, **__
) -> HTTPResponse:
    """Exception handler returns error in json format."""
    status_code = getattr(exception, "status_code", 500)

    if status_code == 500:
        logger.exception(exception)

    return await jinja.render_async(
        "error.html",
        request,
        status=status_code,
        status_code=status_code,
        message=" ".join(str(arg) for arg in exception.args),
    )
