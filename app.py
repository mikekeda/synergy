import traceback

import aioredis
from sanic import Sanic
from sanic_jinja2 import SanicJinja2
from sanic_session import Session, AIORedisSessionInterface
from aiocache import caches

from template_tags import update_param
from settings import (
    redis_cache_config,
    get_env_var,
)
from gino.ext.sanic import Gino

app = Sanic(__name__)
app.config['SECRET_KEY'] = 'test secret'
app.config['DB_USER'] = get_env_var('DB_USER', 'user_admin')
app.config['DB_PASSWORD'] = get_env_var('DB_PASSWORD', 'user_admin_pasS64!')
app.config['DB_HOST'] = get_env_var('DB_HOST', '127.0.0.1')
app.config['DB_DATABASE'] = get_env_var('DB_NAME', 'users')
app.config['redis'] = 'redis://127.0.0.1/7'
db = Gino()
db.init_app(app)

# Set jinja_env and session_interface to None to avoid code style warning.
app.jinja_env = None

jinja = SanicJinja2(app)

app.jinja_env.globals.update(update_param=update_param)

app.redis = None

session = Session()


# Initialize Redis cache
@app.listener('before_server_start')
async def init_cache(_, __):
    caches.set_config(redis_cache_config)
    app.redis = await aioredis.create_redis_pool(app.config['redis'])
    # init extensions fabrics
    session.init_app(app, interface=AIORedisSessionInterface(app.redis))


@app.listener('after_server_stop')
async def after_server_stop(_, __):
    """ Close all db connection on server stop. """
    app.redis.close()


@app.exception(Exception)
async def exception_handler(request, exception: Exception, **__):
    """ Exception handler returns error in json format. """
    status_code = getattr(exception, "status_code", 500)

    if status_code == 500:
        print("\n".join([str(exception.args), traceback.format_exc()]))

    return jinja.render(
        'error.html',
        request,
        status=status_code,
        status_code=status_code,
        message=''.join(exception.args)
    )


# Serves files from the static folder to the URL /static
app.static('/static', './static')
cache = caches.get('default')
