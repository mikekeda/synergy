from peewee import MySQLDatabase, Model, CharField, ForeignKeyField
from playhouse.hybrid import hybrid_property

from mysql.connector import MySQLConnection, Error

# todo: don't commit this
db = MySQLDatabase('test_task', user='test_admin', password='test_admin_pass')
db_config = {
    'user': 'test_admin',
    'password': 'test_admin_pass',
    'host': '127.0.0.1',
    'database': 'test_task'
}

STATUSES = (
    ('0', 'Inactive'),
    ('1', 'Active'),
)


class BaseModel(Model):
    """BaseModel model"""
    class Meta:
        database = db

    @classmethod
    def my_get(cls, id):
        con = MySQLConnection(**db_config)
        cur = con.cursor()
        obj = None
        try:
            query = "SELECT * FROM `{}` WHERE `id` = '{}' LIMIT 1".format(
                cls.__name__.lower(),
                id
            )
            # todo: check why cur.execute(query, (...)) doesn't work
            cur.execute(query)
            row = cur.fetchone()
            # todo: improve this
            obj_dir = ('id', 'name', 'email', 'phone', 'mobile', 'status')
            props = dict(zip(obj_dir, row))
            obj = cls(**props)

            print(obj)
            print(cls.__dict__.keys())
        except Error as e:
            print(e)
            con.rollback()
        con.close()
        return obj


class User(BaseModel):
    """User model"""
    name = CharField(unique=True)
    email = CharField(index=True)
    phone = CharField(max_length=13, null=True)
    mobile = CharField(max_length=13, null=True)
    status = CharField(max_length=1, choices=STATUSES, default='0')

    @hybrid_property
    def status_label(self):
        if hasattr(self, 'status'):
            return dict(STATUSES)[self.status]
        return ''


class Course(BaseModel):
    """Course model"""
    code = CharField(max_length=8, unique=True)
    name = CharField(index=True)


class UserCourse(BaseModel):
    """User/Course relation model"""
    user = ForeignKeyField(User)
    course = ForeignKeyField(Course)
