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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            self._db_connection = MySQLConnection(**db_config)
            self._db_cur = self._db_connection.cursor()
            print(self._db_cur)
        except Error as e:
            print(e)

    def __del__(self):
        self._db_cur = self._db_connection.close()
        self._db_connection.close()

    def my_get_tables(self):
        print('in')
        try:
            print(self._db_cur.execute("SHOW TABLES").commit())
        except Error:
            self._db_connection.rollback()


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
