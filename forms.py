from sanic_wtf import SanicForm
from wtforms import StringField, SelectField, SelectMultipleField
from wtforms.fields.html5 import EmailField, TelField
from wtforms.validators import Optional, DataRequired, Email, Regexp

from models import User, Course, UserCourse, STATUSES


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
            user_courses = UserCourse.select(user_id=user.id)
            self.courses.data = []
            for user_course in user_courses:
                self.courses.data.append(str(user_course.course_id))

    def save(self, *args, **kwargs):
        user = kwargs.get('obj')
        if user:
            user.email = self.email.data
            user.phone = self.phone.data
            user.mobile = self.mobile.data
            user.status = self.status.data
            user.save()

            UserCourse.delete(user_id=user.id)
            for course_id in self.courses.data:
                # todo: improve this
                UserCourse(user_id=user.id, course_id=course_id).save()
