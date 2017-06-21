from playhouse.hybrid import hybrid_property

from mysql.connector import MySQLConnection, Error
from abc import ABC

# todo: don't commit this
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


class BaseModel(ABC):
    """BaseModel model"""
    id = 0

    def __init__(self, **kwargs):
        for key in kwargs:
            assert (key in dir(type(self))), "{} not valid property".format(key)
            setattr(self, key, kwargs[key])

    @staticmethod
    def props():
        return ['id']

    @classmethod
    def get(cls, **kwargs):
        con = MySQLConnection(**db_config)
        cur = con.cursor()
        obj = None
        try:
            conditions = []
            for key in kwargs:
                assert (key in dir(cls)), "{} not valid property".format(key)
                conditions.append("`{}` = '{}'".format(key, kwargs[key]))
            conditions = ' AND '.join(conditions)

            query = "SELECT * FROM `{}` WHERE {} LIMIT 1".format(
                cls.__name__.lower(),
                conditions
            )
            cur.execute(query)
            row = cur.fetchone()
            if row:
                props = dict(zip(cls.props(), row))
                obj = cls(**props)
        except Error as e:
            print(e)
            con.rollback()
        con.close()

        return obj

    @classmethod
    def select(cls, **kwargs):
        con = MySQLConnection(**db_config)
        cur = con.cursor()
        objs = []
        try:
            conditions = []
            for key in kwargs:
                assert (key in dir(cls)), "{} not valid property".format(key)
                conditions.append("`{}`='{}'".format(key, kwargs[key]))
            conditions = ' AND '.join(conditions)

            if conditions:
                query = "SELECT * FROM `{}` WHERE {}".format(
                    cls.__name__.lower(),
                    conditions
                )
            else:
                query = "SELECT * FROM `{}`".format(
                    cls.__name__.lower(),
                )
            cur.execute(query)
            rows = cur.fetchall()
            for row in rows:
                props = dict(zip(cls.props(), row))
                objs.append(cls(**props))
        except Error as e:
            print(e)
            con.rollback()

        return objs

    def delete_instance(self):
        con = MySQLConnection(**db_config)
        cur = con.cursor()
        result = False
        try:
            # todo: need to remove row from usercourse table
            query = "DELETE FROM `{}` WHERE id=%s".format(self.__class__.__name__.lower())
            result = cur.execute(query, (self.id,))
        except Error as e:
            print(e)
            con.rollback()
        con.close()

        return result

    @classmethod
    def delete(cls, **kwargs):
        con = MySQLConnection(**db_config)
        cur = con.cursor()
        result = False
        try:
            conditions = []
            for key in kwargs:
                assert (key in dir(cls)), "{} not valid property".format(key)
                conditions.append("`{}`='{}'".format(key, kwargs[key]))
            conditions = ' AND '.join(conditions)

            if conditions:
                query = "DELETE FROM `{}` WHERE {}".format(
                    cls.__name__.lower(),
                    conditions
                )
            else:
                query = "DELETE FROM `{}`".format(
                    cls.__name__.lower(),
                )
            result = cur.execute(query)
        except Error as e:
            print(e)
            print(query)
            con.rollback()
        con.close()

        return result

    def save(self):
        con = MySQLConnection(**db_config)
        cur = con.cursor()
        result = False
        try:
            values = []
            dict_values = []
            for key in self.props():
                val = str(getattr(self, key))
                values.append(repr(val))
                if key not in super(type(self), self).props():
                    dict_values.append("`{}`={}".format(key, repr(val)))

            query = "INSERT INTO `{}` ({}) VALUES({}) ON DUPLICATE KEY UPDATE {}".format(
                self.__class__.__name__.lower(),
                ', '.join(self.props()),
                ', '.join(values),
                ', '.join(dict_values),
            )
            result = cur.execute(query)
        except Error as e:
            print(e)
            con.rollback()
        con.close()

        return result


class User(BaseModel):
    """User model"""
    name = ''
    email = ''
    phone = ''
    mobile = ''
    status = 0

    # todo: use @property
    @hybrid_property
    def status_label(self):
        if hasattr(self, 'status'):
            return dict(STATUSES)[self.status]

        return ''

    @staticmethod
    def props():
        props = super(User, User).props()
        props.extend(['name', 'email', 'phone', 'mobile', 'status'])

        return props


class Course(BaseModel):
    """Course model"""
    code = ''
    name = ''

    @staticmethod
    def props():
        props = super(Course, Course).props()
        props.extend(['code', 'name'])

        return props


class UserCourse(BaseModel):
    """User/Course relation model"""
    user_id = 0
    course_id = 0

    @staticmethod
    def props():
        props = super(Course, Course).props()
        props.extend(['user_id', 'course_id'])

        return props
