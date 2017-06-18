from sanic import Sanic
from sanic.views import HTTPMethodView
from sanic.response import json, redirect
from sanic_jinja2 import SanicJinja2
from sanic_session import InMemorySessionInterface

from models import User, Course
from forms import UserForm, UserEditForm

app = Sanic(__name__)
app.config['SECRET_KEY'] = 'test secret'
jinja = SanicJinja2(app)

# todo: use Redis
session_interface = InMemorySessionInterface()


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
    users = list(User.select())
    return jinja.render('users.html', request, users=users)


@app.route("/courses")
async def courses_page(request):
    """Courses list"""
    courses = list(Course.select())
    return jinja.render('courses.html', request, courses=courses)


class UserView(HTTPMethodView):

    def get(self, request, uid=None):
        """User edit/create form"""
        if uid:
            user = User.get(id=uid)
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
        if uid:
            user = User.get(id=uid)
            form = UserEditForm(request, obj=user)
        else:
            form = UserForm(request)

        if form.validate():
            # todo: Continue work from this point
            form.save()
            if uid:
                user = User.get(id=uid)
                user.email = form.email.data
                user.phone = form.phone.data
                user.mobile = form.mobile.data
                user.status = form.status.data
            else:
                user = User(
                    name=form.name.data,
                    email=form.email.data,
                    phone=form.phone.data,
                    mobile=form.mobile.data,
                    status=form.status.data,
                )
            user.save()
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
        User.get(id=uid).delete_instance()

        return json({'message': 'User was deleted'})

app.add_route(UserView.as_view(), '/user/(<uid>?)')

app.run(host="0.0.0.0", port=8000, debug=True)
