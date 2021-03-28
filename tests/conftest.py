import os

from sqlalchemy import insert
from sqlalchemy.ext.asyncio import create_async_engine
import pytest

if os.environ.get("SYNERGY_DB_NAME") is None:
    os.environ["SYNERGY_DB_NAME"] = "test_users"

from settings import SANIC_CONFIG
from views import app
from models import Base, Course, User

app.config["WTF_CSRF_ENABLED"] = False


@pytest.fixture
async def db_setup():
    """ Create test databases and tables before tests run and drop them after. """

    engine = create_async_engine(SANIC_CONFIG["DB_URL"])

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

        # Add test users.
        await conn.execute(
            insert(User).values({"name": "test_user_1", "email": "test1@test.com"})
        )
        await conn.execute(
            insert(User).values({"name": "test_user_2", "email": "test2@test.com"})
        )

        # Add test courses.
        await conn.execute(
            insert(Course).values({"code": "P012345", "name": "Python-Base"})
        )
        await conn.execute(
            insert(Course).values({"code": "P234567", "name": "Python-Database"})
        )
        await conn.execute(insert(Course).values({"code": "H345678", "name": "HTML"}))
        await conn.execute(
            insert(Course).values({"code": "J456789", "name": "Java-Base"})
        )
        await conn.execute(
            insert(Course).values({"code": "JS543210", "name": "JavaScript-Base"})
        )

        await conn.commit()

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
