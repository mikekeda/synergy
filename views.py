import os
import re
import socket

from sanic.exceptions import abort
from sanic.log import logger
from sanic.response import html, json, redirect
from sanic.views import HTTPMethodView

from settings import default_page, default_items_per_page
from app import app, jinja
from forms import UserForm, UserEditForm
from models import db, Course, User, UserCourse


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

    if search:
        query = User.query.where(User.name.contains(search))
    else:
        query = User.query

    users = await query.limit(items_per_page).offset((page - 1) * items_per_page).gino.all()

    pages = ((await db.func.count(User.id).gino.scalar()) - 1) // items_per_page + 1

    rendered_page = jinja.render_string(
        'users.html',
        request,
        users=users,
        pages=pages,
        current_page=page,
        items_per_page=items_per_page,
        search=search,
    )

    return html(rendered_page)


@app.route("/courses")
async def courses_page(request):
    """ Courses list. """
    # Get current page.
    try:
        page = int(request.args.get('page', default_page))
    except ValueError:
        page = default_page

    courses = await Course.query.limit(default_items_per_page).offset((page - 1) * default_items_per_page).gino.all()
    pages = ((await db.func.count(Course.id).gino.scalar()) - 1) // default_items_per_page + 1

    rendered_page = jinja.render_string(
        'courses.html',
        request,
        courses=courses,
        pages=pages,
        current_page=page
    )

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
            user = await User.query.where(User.id == uid).gino.first()
            if not user:
                abort(404)

            courses = await Course.query.where(User.id == uid).gino.all()
            user_courses = await UserCourse.query.where(UserCourse.user_id == uid).gino.all()

            form = UserEditForm(request, obj=user, courses=courses, user_courses=user_courses)
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
        courses = await Course.query.where(User.id == uid).gino.all()
        form = UserEditForm(request, courses=courses) if uid else UserForm(request)

        if form.validate():
            if uid:
                user = await User.query.where(User.id == uid).gino.first()
                if not user:
                    abort(404)

                await form.save(obj=user)

                return redirect("/")
            else:
                user = await form.save()
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
        status, _ = await User.delete.where(User.id == uid).gino.status()
        if status != 'DELETE 0':
            return json({'message': 'User was deleted'})
        else:
            abort(404)


app.add_route(UserView.as_view(), '/user/')
app.add_route(UserView.as_view(), '/user/<uid:int>')


if __name__ == "__main__":
    if app.config['DEBUG']:
        app.run(host="0.0.0.0", port=8000, debug=True)
    else:
        # Remove old socket (is any).
        try:
            os.unlink(app.config['SOCKET_FILE'])
        except FileNotFoundError as e:
            logger.info(f"No old socket file found: {e}")

        # Create socket and run app.
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
            try:
                sock.bind(app.config['SOCKET_FILE'])
                app.run(sock=sock, access_log=False)
            except OSError as e:
                logger.warning(e)
