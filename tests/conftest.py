import os
import pytest

if os.environ.get('SYNERGY_DB_NAME') is None:
    os.environ['SYNERGY_DB_NAME'] = 'test_users'

from settings import get_env_var
from views import app, db
from models import User, Course

app.config['WTF_CSRF_ENABLED'] = False
DB_URL = "asyncpg://{}:{}@{}:5432/{}".format(
    get_env_var('DB_USER', 'user_admin'),
    get_env_var('DB_PASSWORD', 'user_admin_pasS64!'),
    get_env_var('DB_HOST', '127.0.0.1'),
    'test_users'
)


@pytest.yield_fixture
async def setup():
    """ Create test databases and tables before tests run and drop them after. """

    await db.set_bind(DB_URL)

    await db.gino.drop_all()
    await db.gino.create_all()

    # Add test user.
    await User.create(name='test_user_1', email='test@test.com')

    await Course.create(code='P012345', name='Python-Base')
    await Course.create(code='P234567', name='Python-Database')
    await Course.create(code='H345678', name='HTML')
    await Course.create(code='J456789', name='Java-Base')
    await Course.create(code='JS543210', name='JavaScript-Base')
    await db.pop_bind().close()

    yield db

    await db.set_bind(DB_URL, echo=True)
    await db.gino.drop_all()
