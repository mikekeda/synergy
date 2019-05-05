import re

from sanic import Sanic
from sanic.views import HTTPMethodView
from sanic.response import html, json, redirect
from sanic.exceptions import abort
from sanic_jinja2 import SanicJinja2
from sanic_session import RedisSessionInterface
import asyncio_redis
from aiocache import caches

from models import User, Course
from forms import UserForm, UserEditForm
from template_tags import update_param
from settings import (
    redis_session_config,
    redis_cache_config,
    default_page,
    default_items_per_page
)

app = Sanic(__name__)
app.config['SECRET_KEY'] = 'test secret'

# Set jinja_env and session_interface to None to avoid code style warning.
app.jinja_env = None

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

# Pass the getter method for the connection pool into the session.
session_interface = RedisSessionInterface(redis.get_redis_pool)


# Initialize Redis cache
@app.listener('before_server_start')
def init_cache(_, __):
    caches.set_config(redis_cache_config)


@app.middleware('request')
async def add_session_to_request(request):
    # Before each request initialize a session using the client's request.
    await session_interface.open(request)


@app.middleware('response')
async def save_session(request, response):
    # After each request save the session,
    # pass the response to set client cookies.
    try:
        await session_interface.save(request, response)
    except RuntimeError:
        pass

# Serves files from the static folder to the URL /static
app.static('/static', './static')
cache = caches.get('default')


@app.route("/")
async def users_page(request):
    """ Users list. """
    # Get current page, convert to int to prevent SQL injection.
    try:
        page = int(request.args.get('page', default_page))
    except ValueError:
        page = default_page

    # Get amount of items for page, convert to int to prevent SQL injection.
    try:
        items_per_page = int(request.args.get('items', default_items_per_page))
    except ValueError:
        items_per_page = default_items_per_page

    # Get search string.
    search = request.args.get('search', '')
    # For user name only letters are allowed,
    # remove any other charset to prevent SQL injection
    search = re.sub('[^a-zA-Z]+', '', search)

    # Try to get page from the cache (if it's not search result).
    key = '_'.join(['users', str(page), str(items_per_page)])
    try:
        rendered_page = await cache.get(key) if not search else None
    except RuntimeError:
        rendered_page = None

    if not rendered_page:
        if search:
            users = User.select().where(
                User.name.contains(search)
            ).paginate(page, items_per_page)
        else:
            users = User.select().paginate(page, items_per_page)
        pages = (User.select().count(None) - 1) // items_per_page + 1

        rendered_page = jinja.render_string(
            'users.html',
            request,
            users=users,
            pages=pages,
            current_page=page,
            items_per_page=items_per_page,
            search=search,
        )
        # Set page cache (no need to set search results).
        if not search:
            try:
                await cache.set(key, rendered_page)
            except RuntimeError:
                pass
    return html(rendered_page)


@app.route("/courses")
async def courses_page(request):
    """ Courses list. """
    # Get current page.
    try:
        page = int(request.args.get('page', default_page))
    except ValueError:
        page = default_page

    # Try to get page from the cache.
    key = '_'.join(['courses', str(page), str(default_items_per_page)])
    try:
        rendered_page = await cache.get(key)
    except RuntimeError:
        rendered_page = None

    if not rendered_page:
        courses = Course.select().paginate(page, default_items_per_page)
        pages = (Course.select().count(None) - 1) // default_items_per_page + 1

        rendered_page = jinja.render_string(
            'courses.html',
            request,
            courses=courses,
            pages=pages,
            current_page=page
        )
        # Set page cache.
        try:
            await cache.set(key, rendered_page)
        except RuntimeError:
            pass
    return html(rendered_page)


@app.route("/about")
async def about_page(request):
    """ About page. """
    return html(jinja.render_string('about.html', request))


class UserView(HTTPMethodView):

    # noinspection PyMethodMayBeStatic
    async def get(self, request, uid: int = None):
        """ User edit/create form. """
        if uid:
            uid = int(uid)
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
            new=not uid
        )

    # noinspection PyMethodMayBeStatic
    async def post(self, request, uid: int = None):
        """ Submit for User edit/create form. """
        # TODO: Impalement ajax form submit
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

    # noinspection PyMethodMayBeStatic
    async def delete(self, _, uid: int):
        """ User deletion. """
        try:
            user = User.get(User.id == uid)
            user.delete_instance(recursive=True)
            return json({'message': 'User was deleted'})
        except User.DoesNotExist:
            abort(404)


app.add_route(UserView.as_view(), '/user/')
app.add_route(UserView.as_view(), '/user/<uid:int>')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
