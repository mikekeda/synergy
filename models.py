import enum

from sqlalchemy import Column, Integer, Enum, ForeignKey, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Status(enum.Enum):
    inactive = "Inactive"
    active = "Active"


class User(Base):
    """ User model. """

    __tablename__ = "user"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    email = Column(String, nullable=False, index=True)
    phone = Column(String(13))
    mobile = Column(String(13))
    status = Column(Enum(Status), nullable=False, default=Status.inactive)


class Course(Base):
    """ Course model. """

    __tablename__ = "course"

    id = Column(Integer, primary_key=True)
    code = Column(String(8), unique=True)
    name = Column(String, index=True)


class UserCourse(Base):
    """ User/Course relation model. """

    __tablename__ = "usercourse"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"))
    course_id = Column(Integer, ForeignKey("course.id", ondelete="CASCADE"))
