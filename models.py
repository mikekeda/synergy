import asyncio

from peewee import (PostgresqlDatabase, Model, IntegrityError,
                    CharField, ForeignKeyField)
from aiocache import caches

from settings import db_config, default_page, default_items_per_page

database = PostgresqlDatabase(**db_config)

STATUSES = (
    ('0', 'Inactive'),
    ('1', 'Active'),
)

cache = caches.get('default')


class BaseModel(Model):
    """ Base class with common methods. """
    class Meta:
        database = database

    def save(self, force_insert=False, only=None):
        try:
            rows = super().save(force_insert=force_insert, only=only)
            # Asynchronously delete class and object cache.
            asyncio.ensure_future(type(self).clean_cache(self.id))

            return rows
        except IntegrityError:
            database.rollback()
            return None

    def delete_instance(self, recursive=False, delete_nullable=False):
        counter = super().delete_instance(recursive=recursive,
                                          delete_nullable=delete_nullable)
        # Asynchronously delete class and object cache.
        asyncio.ensure_future(type(self).clean_cache(self.id))
        return counter

    @classmethod
    def props(cls):
        return [key for key in cls._meta.fields.keys() if key != 'id']

    @staticmethod
    def _foreign_classes():
        return []

    @classmethod
    async def clean_cache(cls, obj_id=None):
        """ Delete cache keys those are related to the class and obj_id. """
        class_name = cls.__name__.lower()

        # Probably user will be redirected to page which is using this cache,
        # so we need to clean it first.
        await cache.delete('{}s_{}_{}_'.format(
            class_name,
            default_page,
            default_items_per_page,
        ))

        if obj_id:
            # Delete specific object cache if obj_id was provided.
            keys = await cache.raw('keys', '{}_{}'.format(class_name, obj_id))
        else:
            # Not sure which object was modified, so delete all object caches.
            keys = await cache.raw('keys', '{}_*'.format(class_name))

        for key in keys:
            await cache.delete(key)

        # Delete pages caches
        keys = await cache.raw('keys', '{}s_*'.format(class_name))
        for key in keys:
            await cache.delete(key)

        for class_name in cls._foreign_classes():
            cl = globals()[class_name]
            cl.clean_cache()

    @classmethod
    async def _set_cache(cls, obj):
        """ Save object to cache. """
        return await cache.set(
            '{}_{}'.format(cls.__name__.lower(), obj.id),
            obj
        )

    @classmethod
    async def get_from_cache(cls, obj_id):
        """ Get object from cache. """
        try:
            obj = await cache.get('{}_{}'.format(cls.__name__.lower(), obj_id))
        except RuntimeError:
            obj = None

        return obj


class User(BaseModel):
    """ User model. """
    name = CharField(unique=True)
    email = CharField(index=True)
    phone = CharField(max_length=13, null=True)
    mobile = CharField(max_length=13, null=True)
    status = CharField(max_length=1, choices=STATUSES, default='0')

    @staticmethod
    def _foreign_classes():
        return ['UserCourse']


class Course(BaseModel):
    """ Course model. """
    code = CharField(max_length=8, unique=True)
    name = CharField(index=True)

    @staticmethod
    def _foreign_classes():
        return ['UserCourse']


class UserCourse(BaseModel):
    """ User/Course relation model. """
    user = ForeignKeyField(User)
    course = ForeignKeyField(Course)


MODELS = [User, Course, UserCourse]
