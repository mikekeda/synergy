from mysql.connector import MySQLConnection, Error

from settings import db_config

STATUSES = (
    ('0', 'Inactive'),
    ('1', 'Active'),
)
# todo: add more comments


class BaseModel:
    """BaseModel model"""
    id = 0

    def __init__(self, **kwargs):
        for key in kwargs:
            assert (key in dir(type(self))), "{} not a property".format(key)
            setattr(self, key, kwargs[key])

    @staticmethod
    def props():
        return ['id']

    @staticmethod
    def _foreign_classes():
        return []

    @classmethod
    def get(cls, id):
        con = MySQLConnection(**db_config)
        cur = con.cursor()
        obj = None
        try:
            cur.callproc(
                'get_object',
                args=(cls.__name__.lower(), id)
            )
            results = list(cur.stored_results())
            row = results[0].fetchone()
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
        objs = {
            'objects': [],
            'total': 0,
        }
        try:
            limit = kwargs['limit'] if 'limit' in kwargs else 15
            page = kwargs['page'] if 'page' in kwargs else 1
            offset = (page - 1) * limit
            cur.callproc(
                'select_objects',
                args=(cls.__name__.lower(), limit, offset)
            )
            results = list(cur.stored_results())
            rows = results[0].fetchall()
            objs['total'] = results[1].fetchone()[0]
            for row in rows:
                props = dict(zip(cls.props(), row))
                objs['objects'].append(cls(**props))
        except Error as e:
            print(e)
            con.rollback()

        return objs

    @classmethod
    def delete(cls, **kwargs):
        con = MySQLConnection(**db_config)
        cur = con.cursor()
        result = False
        try:
            # for now only first condition will be taken
            key, value = kwargs.popitem()
            assert (key in dir(cls)), "{} not valid property".format(key)

            # delete all rows where are foreign key to current object
            if key == 'id':
                for class_name in cls._foreign_classes():
                    cl = globals()[class_name]
                    condition = {
                        '{}_id'.format(cls.__name__.lower()): value
                    }
                    cl.delete(**condition)

            cur.callproc(
                'delete_objects',
                args=(cls.__name__.lower(), key, value)
            )
            con.commit()
            result = True
        except Error as e:
            print(e)
            con.rollback()
        con.close()

        return result

    def save(self):
        con = MySQLConnection(**db_config)
        cur = con.cursor()
        result = False
        try:
            dict_values = {}
            for key in self.props():
                if key not in super(type(self), self).props():
                    dict_values[key] = getattr(self, key)

            if self.id == 0:
                # new object, need to insert row
                values = []
                for key in dict_values:
                    values.append("'{}'".format(dict_values[key]))

                cur.callproc(
                    'insert_object',
                    args=(
                        type(self).__name__.lower(),
                        ','.join(dict_values.keys()),
                        ','.join(values),
                    )
                )
            else:
                # need to update row
                values = []
                for key in dict_values:
                    values.append("{}='{}'".format(key, dict_values[key]))

                cur.callproc(
                    'update_object',
                    args=(
                        type(self).__name__.lower(),
                        ','.join(values),
                        self.id,
                    )
                )

            con.commit()
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

    @property
    def status_label(self):
        if hasattr(self, 'status'):
            return dict(STATUSES)[self.status]

        return ''

    @staticmethod
    def props():
        props = super(User, User).props()
        props.extend(['name', 'email', 'phone', 'mobile', 'status'])

        return props

    @staticmethod
    def _foreign_classes():
        return ['UserCourse']

    @classmethod
    def select(cls, **kwargs):
        con = MySQLConnection(**db_config)
        cur = con.cursor()
        objs = {
            'objects': [],
            'total': 0,
        }
        try:
            limit = kwargs['limit'] if 'limit' in kwargs else 15
            page = kwargs['page'] if 'page' in kwargs else 1
            search = kwargs['search'] if 'search' in kwargs else None
            search = search if search != '' else None
            offset = (page - 1) * limit
            cur.callproc(
                'select_users',
                args=(cls.__name__.lower(), offset, limit, search)
            )
            results = list(cur.stored_results())
            rows = results[0].fetchall()
            objs['total'] = results[1].fetchone()[0]
            for row in rows:
                props = dict(zip(cls.props(), row))
                objs['objects'].append(cls(**props))
        except Error as e:
            print(e)
            con.rollback()

        return objs


class Course(BaseModel):
    """Course model"""
    code = ''
    name = ''

    @staticmethod
    def props():
        props = super(Course, Course).props()
        props.extend(['code', 'name'])

        return props

    @staticmethod
    def _foreign_classes():
        return ['UserCourse']


class UserCourse(BaseModel):
    """User/Course relation model"""
    user_id = 0
    course_id = 0

    @staticmethod
    def props():
        props = super(Course, Course).props()
        props.extend(['user_id', 'course_id'])

        return props

    @classmethod
    def select(cls, **kwargs):
        con = MySQLConnection(**db_config)
        cur = con.cursor()
        objs = []
        try:
            limit = kwargs['limit'] if 'limit' in kwargs else 15
            page = kwargs['page'] if 'page' in kwargs else 1
            offset = (page - 1) * limit
            user_id = kwargs['user_id'] if 'user_id' in kwargs else None
            cur.callproc(
                'select_usercourses',
                args=(cls.__name__.lower(), offset,  limit, user_id)
            )
            results = list(cur.stored_results())
            rows = results[0].fetchall()
            for row in rows:
                props = dict(zip(cls.props(), row))
                objs.append(cls(**props))
        except Error as e:
            print(e)
            con.rollback()

        return objs
