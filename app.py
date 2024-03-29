from aiocache import caches
import aioredis
from sanic import Sanic
from sanic.log import logger
from sanic.request import Request
from sanic.response import HTTPResponse
from sanic_jinja2 import SanicJinja2
from sanic_session import Session, AIORedisSessionInterface
from sqlalchemy.ext.asyncio import create_async_engine

from template_tags import update_param
from settings import redis_cache_config, SANIC_CONFIG

app = Sanic(__name__)
app.config.update(SANIC_CONFIG)
app.static("/static", "./static")

jinja = SanicJinja2(app, autoescape=True, enable_async=True)
jinja.env.globals["update_param"] = update_param

session = Session()


@app.listener("before_server_start")
async def before_server_start(_app, _):
    """Initialize database connection and Redis cache."""
    _app.ctx.engine = create_async_engine(SANIC_CONFIG["DB_URL"])

    caches.set_config(redis_cache_config)
    _app.ctx.redis = await aioredis.Redis.from_url(_app.config["redis"])
    # init extensions fabrics
    session.init_app(
        _app,
        interface=AIORedisSessionInterface(
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
