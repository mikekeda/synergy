from sanic_wtf import SanicForm
from wtforms import StringField, SelectField, SelectMultipleField
from wtforms.fields.html5 import EmailField, TelField
from wtforms.validators import Optional, DataRequired, Email, Regexp

from models import User, Course, UserCourse, STATUSES

# todo: Remove this
COURSES = (
    ('P012345', 'Python-Base'),
    ('P234567', 'Python-Database'),
    ('H345678', 'HTML'),
    ('J456789', 'Java-Base'),
    ('JS543210', 'JavaScript-Base'),
)


class UserForm(SanicForm):
    """User create form"""
    name = StringField('Name', validators=[DataRequired()])
    email = EmailField('E-mail', validators=[
        DataRequired(),
        Email(message='Please enter a valid email address!'),
    ])
    phone = TelField('Phone', validators=[
        Optional(),
        Regexp(
            '^\+?[0-9]{3}-?[0-9]{6,12}$',
            message='Please enter a valid phone number!'
        ),
    ])
    mobile = TelField('Mobile phone', validators=[
        Optional(),
        Regexp(
            '^\+?[0-9]{3}-?[0-9]{6,12}$',
            message='Please enter a valid phone number!'
        ),
    ])
    status = SelectField('Status', choices=STATUSES)

    def save(self, *args, **kwargs):
        # todo: Improve this
        user = User(
            name=self.name.data,
            email=self.email.data,
            phone=self.phone.data,
            mobile=self.mobile.data,
            status=self.status.data,
        )
        user.save()

        return user


class UserEditForm(UserForm):
    """User edit form"""
    courses = SelectMultipleField('Courses')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # list of courses
        courses = [('', '-- select courses --')]
        courses.extend(
            [(str(course.id), course.name) for course in Course.select()]
        )
        self.courses.choices = courses

        # user's courses
        user = kwargs.get('obj')
        if user:
            # todo: need to set user's courses
            usercourses = list(UserCourse.select().where(
                UserCourse.user == user.id
            ))
            # todo: improve CS
            self.courses.data = tuple([usercourse.course.id for usercourse in usercourses])

    def save(self, *args, **kwargs):
        user = kwargs.get('obj')
        if user:
            user.email = self.email.data
            user.phone = self.phone.data
            user.mobile = self.mobile.data
            user.status = self.status.data
            user.save()

            user_courses = UserCourse.select().where(
                UserCourse.user == user.id
            )
            # todo: improve this
            UserCourse(user=user.id, course=1).save()
