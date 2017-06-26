from mysql.connector import MySQLConnection, Error

# todo: don't commit this
db_config = {
    'user': 'test_admin',
    'password': 'test_admin_pass',
    'host': '127.0.0.1',
    'database': 'Users'
}

STATUSES = (
    ('0', 'Inactive'),
    ('1', 'Active'),
)


class BaseModel():
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
    def get(cls, **kwargs):
        con = MySQLConnection(**db_config)
        cur = con.cursor()
        obj = None
        try:
            conditions = []
            for key in kwargs:
                assert (key in dir(cls)), "{} not valid property".format(key)
                conditions.append("{}=%s".format(key))
            conditions = ' AND '.join(conditions)

            query = "SELECT * FROM `{}` WHERE {} LIMIT 1".format(
                cls.__name__.lower(),
                conditions
            )
            cur.execute(query, list(kwargs.values()))
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
            # todo: add search by username and paginate
            # todo: add filter UserCourse by user_id
            limit = kwargs['limit'] if 'limit' in kwargs else 15
            offset = kwargs['offset'] if 'offset' in kwargs else 0
            cur.callproc(
                'select_objects',
                args=(cls.__name__.lower(), limit, offset)
            )
            objects = next(cur.stored_results())
            rows = objects.fetchall()
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
            for class_name in self._foreign_classes():
                cl = globals()[class_name]
                condition = {
                    '{}_id'.format(type(self).__name__.lower()): self.id
                }
                cl.delete(**condition)

            query = "DELETE FROM `{}` WHERE id=%s".format(
                self.__class__.__name__.lower()
            )
            result = cur.execute(query, (self.id,))
            con.commit()
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
                conditions.append("{}=%s".format(key))
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
            result = cur.execute(query, list(kwargs.values()))
            con.commit()
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
            insert_values = []
            update_values = []
            dict_update_values = {}
            for key in self.props():
                val = getattr(self, key)
                insert_values.append(val)
                if key not in super(type(self), self).props():
                    dict_update_values[key] = val
                    update_values.append(val)

            query = """
            INSERT INTO `{}` ({}) VALUES({}) ON DUPLICATE KEY UPDATE {}
            """.format(
                self.__class__.__name__.lower(),
                ','.join(self.props()),
                ','.join(['%s' for _ in insert_values]),
                ','.join(["{}=%s".format(key) for key in dict_update_values]),
            )
            result = cur.execute(query, insert_values + update_values)
            con.commit()
        except Error as e:
            print(e)
            print(cur._executed)
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
