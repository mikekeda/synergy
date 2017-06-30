from sanic import Sanic
from sanic.views import HTTPMethodView
from sanic.response import json, redirect
from sanic_jinja2 import SanicJinja2
from sanic_session import RedisSessionInterface
import asyncio_redis
import aiocache
from aiocache import RedisCache, cached
from aiocache.serializers import StringSerializer
import re

from models import User, Course
from forms import UserForm, UserEditForm
from template_tags import update_param

app = Sanic(__name__)
app.config['SECRET_KEY'] = 'test secret'
jinja = SanicJinja2(app)
cache = RedisCache(db=4)

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
                host='localhost', port=6379, db=4, poolsize=10
            )

        return self._pool


redis = Redis()

# pass the getter method for the connection pool into the session
session_interface = RedisSessionInterface(redis.get_redis_pool)


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
    await cache.set('key', 'value')
    # get current page, convert to int to prevent SQL injection
    try:
        page = int(request.args.get('page', 1))
    except ValueError:
        page = 1

    # get amount of items for a page, convert to int to prevent SQL injection
    try:
        items_per_page = int(request.args.get('items', 15))
    except ValueError:
        items_per_page = 15

    # get search string
    search = request.args.get('search', '')
    # for user name only letters are allowed
    # remove any other charset to prevent SQL injection
    search = re.sub('[^a-zA-Z]+', '', search)

    users = User.select(page=page, limit=items_per_page, search=search)
    pages = (users['total'] - 1) // items_per_page + 1

    return jinja.render(
        'users.html',
        request,
        users=users['objects'],
        pages=pages,
        current_page=page,
        items_per_page=items_per_page,
        search=search,
    )


@app.route("/courses")
async def courses_page(request):
    """Courses list"""
    # max 15 courses on page
    items_per_page = 15
    # get current page
    try:
        page = int(request.args.get('page', 1))
    except ValueError:
        page = 1

    courses = Course.select(page=page, limit=items_per_page)
    pages = (courses['total'] - 1) // items_per_page + 1

    return jinja.render(
        'courses.html',
        request,
        courses=courses['objects'],
        pages=pages,
        current_page=page
    )


class UserView(HTTPMethodView):

    def get(self, request, uid=None):
        """User edit/create form"""
        if uid:
            user = User.get(uid)
            form = UserEditForm(request, obj=user)
        else:
            form = UserForm(request)

        return jinja.render(
            'user-form.html',
            request,
            form=form,
            new=uid == ''
        )

    def post(self, request, uid=None):
        """Submit for User edit/create form"""
        # todo: impalement ajax form submit
        form = UserEditForm(request) if uid else UserForm(request)

        if form.validate():
            if uid:
                user = User.get(uid)
                form.save(obj=user)
            else:
                form.save()
        else:
            return jinja.render(
                'user-form.html',
                request,
                form=form,
                new=uid == ''
            )

        return redirect("/")

    def delete(self, request, uid):
        """User deletion"""
        User.delete(id=uid)

        return json({'message': 'User was deleted'})

app.add_route(UserView.as_view(), '/user/(<uid>?)')

app.run(host="0.0.0.0", port=8000, debug=True)
