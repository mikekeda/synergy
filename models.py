from enum import Enum

from app import db


class Status(Enum):
    inactive = "Inactive"
    active = "Active"


class User(db.Model):
    """ User model. """

    __tablename__ = "user"

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String, nullable=False, unique=True)
    email = db.Column(db.String, nullable=False, index=True)
    phone = db.Column(db.String(13))
    mobile = db.Column(db.String(13))
    status = db.Column(db.Enum(Status), nullable=False, default=Status.inactive)


class Course(db.Model):
    """ Course model. """

    __tablename__ = "course"

    id = db.Column(db.Integer(), primary_key=True)
    code = db.Column(db.String(8), unique=True)
    name = db.Column(db.String, index=True)


class UserCourse(db.Model):
    """ User/Course relation model. """

    __tablename__ = "usercourse"

    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    course_id = db.Column(db.Integer, db.ForeignKey("course.id"))
