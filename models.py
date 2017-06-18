from peewee import MySQLDatabase, Model, CharField, ForeignKeyField
from playhouse.hybrid import hybrid_property

# todo: don't commit this
db = MySQLDatabase('test_task', user='test_admin', password='test_admin_pass')

STATUSES = (
    ('0', 'Inactive'),
    ('1', 'Active'),
)


class BaseModel(Model):
    """BaseModel model"""
    class Meta:
        database = db


class User(BaseModel):
    """User model"""
    name = CharField(unique=True)
    email = CharField(index=True)
    phone = CharField(max_length=13, null=True)
    mobile = CharField(max_length=13, null=True)
    status = CharField(max_length=1, choices=STATUSES, default='0')

    @hybrid_property
    def status_label(self):
        return dict(STATUSES)[self.status]


class Course(BaseModel):
    """Course model"""
    code = CharField(max_length=8, unique=True)
    name = CharField(index=True)


class UserCourse(BaseModel):
    """User/Course relation model"""
    user = ForeignKeyField(User)
    course = ForeignKeyField(Course)
