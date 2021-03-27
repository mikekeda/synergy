import os
import re
import socket

from sanic.exceptions import abort
from sanic.log import logger
from sanic.request import Request
from sanic.response import json, redirect
from sanic.views import HTTPMethodView

from settings import default_page, default_items_per_page
from app import app, jinja
from forms import UserForm, UserEditForm
from models import db, Course, User, UserCourse


def get_arg(request: Request, arg: str, _type: type, default):
    """ Get request argument. """
    try:
        return _type(request.args.get(arg, default))
    except ValueError:
        pass

    return default


@app.route("/")
async def users_page(request: Request):
    """ Users list. """
    # Get current page, convert to int to prevent SQL injection.
    page = get_arg(request, "page", int, default_page)
    items_per_page = get_arg(request, "items", int, default_items_per_page)

    # Get search string.
    search = request.args.get("search", "")
    # For user name only letters are allowed,
    # remove any other charset to prevent SQL injection
    search = re.sub("[^a-zA-Z]+", "", search)

    query = User.query
    if search:
        query = query.where(User.name.contains(search))

    users = (
        await query.limit(items_per_page).offset((page - 1) * items_per_page).gino.all()
    )

    pages = ((await db.func.count(User.id).gino.scalar()) - 1) // items_per_page + 1

    return await jinja.render_async(
        "users.html",
        request,
        users=users,
        pages=pages,
        current_page=page,
        items_per_page=items_per_page,
        search=search,
    )


@app.route("/courses")
async def courses_page(request: Request):
    """ Courses list. """
    # Get current page.
    page = get_arg(request, "page", int, default_page)

    courses = (
        await Course.query.limit(default_items_per_page)
        .offset((page - 1) * default_items_per_page)
        .gino.all()
    )
    pages = (
        (await db.func.count(Course.id).gino.scalar()) - 1
    ) // default_items_per_page + 1

    return await jinja.render_async(
        "courses.html", request, courses=courses, pages=pages, current_page=page
    )


@app.route("/about")
async def about_page(request: Request):
    """ About page. """
    return await jinja.render_async("about.html", request)


class UserView(HTTPMethodView):

    # noinspection PyMethodMayBeStatic
    async def get(self, request: Request, uid: int = None):
        """ User edit/create form. """
        if uid:
            user = await User.query.where(User.id == uid).gino.first()
            if not user:
                abort(404)

            courses = await Course.query.gino.all()
            user_courses = await UserCourse.query.where(
                UserCourse.user_id == uid
            ).gino.all()

            form = UserEditForm(
                request, obj=user, courses=courses, user_courses=user_courses
            )
        else:
            form = UserForm(request)

        return await jinja.render_async(
            "user-form.html", request, form=form, new=not uid
        )

    # noinspection PyMethodMayBeStatic
    async def post(self, request: Request, uid: int = None):
        """ Submit for User edit/create form. """
        # TODO: Impalement ajax form submit
        if uid:
            courses = await Course.query.gino.all()
            form = UserEditForm(request, courses=courses)
            if form.validate():
                user = await User.query.where(User.id == uid).gino.first()
                if not user:
                    abort(404)

                await form.save(obj=user)

                return redirect("/")
        else:
            form = UserForm(request)
            if form.validate():
                user = await form.save()
                if user:
                    return redirect("/")
                else:
                    form.name.errors.append("This username already taken!")

        return await jinja.render_async(
            "user-form.html", request, form=form, new=uid == ""
        )

    # noinspection PyMethodMayBeStatic
    async def delete(self, _, uid: int):
        """ User deletion. """
        status, _ = await User.delete.where(User.id == uid).gino.status()
        if status == "DELETE 0":
            abort(404)

        return json({"message": "User was deleted"})


app.add_route(UserView.as_view(), "/user/")
app.add_route(UserView.as_view(), "/user/<uid:int>")


if __name__ == "__main__":
    if app.config["DEBUG"]:
        app.run(host="127.0.0.1", port=8000, debug=True)
    else:
        # Remove old socket (is any).
        try:
            os.unlink(app.config["SOCKET_FILE"])
        except FileNotFoundError as e:
            logger.info(f"No old socket file found: {e}")

        # Create socket and run app.
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
            try:
                sock.bind(app.config["SOCKET_FILE"])
                app.run(sock=sock, access_log=False)
            except OSError as e:
                logger.warning(e)
