from sanic_wtf import SanicForm
from wtforms import StringField, SelectField, SelectMultipleField
from wtforms.fields.html5 import EmailField, TelField
from wtforms.validators import Optional, DataRequired, Email, Regexp

from models import User, UserCourse, Status


class UserForm(SanicForm):
    """ User create form. """

    name = StringField(
        "Name",
        validators=[
            DataRequired(),
            Regexp("^[a-zA-Z]+$", message="Only letters allowed!"),
        ],
    )
    email = EmailField(
        "E-mail",
        validators=[
            DataRequired(),
            Email(message="Please enter a valid email address!"),
        ],
    )
    phone = TelField(
        "Phone",
        validators=[
            Optional(),
            Regexp(
                "^\\+?[0-9]{3}-?[0-9]{6,12}$",
                message="Please enter a valid phone number!",
            ),
        ],
    )
    mobile = TelField(
        "Mobile phone",
        validators=[
            Optional(),
            Regexp(
                "^\\+?[0-9]{3}-?[0-9]{6,12}$",
                message="Please enter a valid mobile number!",
            ),
        ],
    )
    status = SelectField("Status", choices=[(s.name, s.value) for s in Status])

    async def save(self, *args, **kwargs):
        user = await User.create(
            **{
                key: getattr(self, key).data
                for key in self._fields
                if hasattr(User, key)
            }
        )

        return user


class UserEditForm(UserForm):
    """ User edit form. """

    courses = SelectMultipleField("Courses")

    def __init__(self, request=None, *args, **kwargs):
        super().__init__(request, *args, **kwargs)

        if kwargs.get("obj"):
            self.status.data = kwargs["obj"].status.name

        if kwargs.get("courses"):
            # List of courses.
            self.courses.choices = [("", "-- select courses --")]
            self.courses.choices.extend(
                [(str(course.id), course.name) for course in kwargs["courses"]]
            )

            # User's courses.
            user_courses = kwargs.get("user_courses")
            if user_courses:
                self.courses.data = []
                for user_course in user_courses:
                    self.courses.data.append(str(user_course.course_id))

    async def save(self, *args, **kwargs):
        """ Form save. """
        user = kwargs.get("obj")
        if user:
            await user.update(
                **{
                    key: getattr(self, key).data
                    for key in self._fields
                    if getattr(user, key, None)
                }
            ).apply()

            await UserCourse.delete.where(UserCourse.user_id == user.id).gino.status()
            for course_id in self.courses.data:
                await UserCourse.create(user_id=user.id, course_id=int(course_id))
