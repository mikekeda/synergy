from peewee import SqliteDatabase, Model, CharField, BooleanField

db = SqliteDatabase('my_app.db')


class BaseModel(Model):
    class Meta:
        database = db


class User(BaseModel):
    name = CharField()
    email = CharField()
    staus = BooleanField(default=False)
