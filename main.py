from sanic import Sanic
from sanic.views import HTTPMethodView
from sanic.response import html, json, redirect
from sanic.exceptions import abort
from sanic_jinja2 import SanicJinja2
from sanic_session import RedisSessionInterface
import asyncio_redis
from aiocache import caches
import re

from models import User, Course
from forms import UserForm, UserEditForm
from template_tags import update_param
from settings import redis_session_config, redis_cache_config
from settings import default_page, default_items_per_page

app = Sanic(__name__)
app.config['SECRET_KEY'] = 'test secret'
jinja = SanicJinja2(app)

app.jinja_env.globals.update(update_param=update_param)


class Redis:
    """
    A simple wrapper class that allows you to share a connection
    pool across your application.
    """
    _pool = None

    async def get_redis_pool(self):
        if not self._pool:
            self._pool = await asyncio_redis.Pool.create(
                **redis_session_config
            )

        return self._pool


redis = Redis()

# pass the getter method for the connection pool into the session
session_interface = RedisSessionInterface(redis.get_redis_pool)


# Initialize Redis cache
@app.listener('before_server_start')
def init_cache(sanic, loop):
    caches.set_config(redis_cache_config)


@app.middleware('request')
async def add_session_to_request(request):
    # before each request initialize a session
    # using the client's request
    await session_interface.open(request)


@app.middleware('response')
async def save_session(request, response):
    # after each request save the session,
    # pass the response to set client cookies
    await session_interface.save(request, response)

# Serves files from the static folder to the URL /static
app.static('/static', './static')


@app.route("/")
async def users_page(request):
    """Users list"""
    # get current page, convert to int to prevent SQL injection
    try:
        page = int(request.args.get('page', default_page))
    except ValueError:
        page = default_page

    # get amount of items for page, convert to int to prevent SQL injection
    try:
        items_per_page = int(request.args.get('items', default_items_per_page))
    except ValueError:
        items_per_page = default_items_per_page

    # get search string
    search = request.args.get('search', '')
    # for user name only letters are allowed
    # remove any other charset to prevent SQL injection
    search = re.sub('[^a-zA-Z]+', '', search)

    # try to get page from the cache
    cache = caches.get('default')
    # todo: maybe not need use cache if there is search
    key = '_'.join(['users', str(page), str(items_per_page), search])
    rendered_page = await cache.get(key)

    if not rendered_page:
        if search:
            users = User.select().where(
                User.name.contains(search)
            ).paginate(page, items_per_page)
        else:
            users = User.select().paginate(page, items_per_page)
        pages = (User.select().count() - 1) // items_per_page + 1

        rendered_page = jinja.render_string(
            'users.html',
            request,
            users=users,
            pages=pages,
            current_page=page,
            items_per_page=items_per_page,
            search=search,
        )
        # set page cache
        await cache.set(key, rendered_page)
    return html(rendered_page)


@app.route("/courses")
async def courses_page(request):
    """Courses list"""
    # get current page
    try:
        page = int(request.args.get('page', default_page))
    except ValueError:
        page = default_page

    # try to get page from the cache
    cache = caches.get('default')
    key = '_'.join(['courses', str(page), str(default_items_per_page)])
    rendered_page = await cache.get(key)

    if not rendered_page:
        courses = Course.select().paginate(page, default_items_per_page)
        pages = (Course.select().count() - 1) // default_items_per_page + 1

        rendered_page = jinja.render_string(
            'courses.html',
            request,
            courses=courses,
            pages=pages,
            current_page=page
        )
        # set page cache
        await cache.set(key, rendered_page)
    return html(rendered_page)


class UserView(HTTPMethodView):
    async def get(self, request, uid=None):
        """User edit/create form"""
        if uid:
            user = await User.get_from_cache(uid)
            if not user:
                try:
                    user = User.get(User.id == uid)
                except User.DoesNotExist:
                    abort(404)
            form = UserEditForm(request, obj=user)
        else:
            form = UserForm(request)

        return jinja.render(
            'user-form.html',
            request,
            form=form,
            new=uid == ''
        )

    async def post(self, request, uid=None):
        """Submit for User edit/create form"""
        # todo: impalement ajax form submit
        form = UserEditForm(request) if uid else UserForm(request)

        if form.validate():
            if uid:
                user = await User.get_from_cache(uid)
                if not user:
                    try:
                        user = User.get(User.id == uid)
                    except User.DoesNotExist:
                        abort(404)
                form.save(obj=user)

                return redirect("/")
            else:
                user = form.save()
                if user:
                    return redirect("/")
                else:
                    form.name.errors.append('This username already taken!')

        return jinja.render(
            'user-form.html',
            request,
            form=form,
            new=uid == ''
        )

    async def delete(self, request, uid):
        """User deletion"""
        try:
            user = User.get(User.id == uid)
        except User.DoesNotExist:
            abort(404)

        user.delete_instance(recursive=True)

        return json({'message': 'User was deleted'})


app.add_route(UserView.as_view(), '/user/(<uid>?)')

app.run(host="0.0.0.0", port=8080)
