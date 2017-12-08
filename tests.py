import os

if os.environ.get('SYNERGY_DB_NAME') is None:
    os.environ['SYNERGY_DB_NAME'] = 'test_users'

# from unittest.mock import patch, Mock, MagicMock
# from unittest.mock import ANY
from urllib.parse import urlencode

from main import app
from models import User, Course, MODELS


for cls in MODELS:
    cls.drop_table(fail_silently=True, cascade=True)
    cls.create_table(fail_silently=True)

# Add test user.
User(name='test_user_1', email='test@test.com').save()

# Add test courses.
test_courses = (
    ('P012345', 'Python-Base'),
    ('P234567', 'Python-Database'),
    ('H345678', 'HTML'),
    ('J456789', 'Java-Base'),
    ('JS543210', 'JavaScript-Base'),
)

for code, name in test_courses:
    Course(code=code, name=name).save()

app.config['WTF_CSRF_ENABLED'] = False


# Tests.
def test_home_page():
    request, response = app.test_client.get('/')
    assert response.status == 200

    request, response = app.test_client.get('/?items=10')
    assert response.status == 200

    request, response = app.test_client.get('/?items=20&search=t')
    assert response.status == 200


def test_courses_page():
    request, response = app.test_client.get('/courses')
    assert response.status == 200


def test_user_page_get():
    request, response = app.test_client.get('/user/')
    assert response.status == 200


# @patch('sanic_jinja2.SanicJinja2.render', new=Mock())
# def test_user_page_post():
#     with patch('sanic_jinja2.SanicJinja2.render') as fake_render:
#         data = {
#             'name': 'testname',
#             'email': 'test_email1@test.com',
#             'phone': '0999999999',
#             'mobile': '0999999999',
#             'status': '1'
#         }
#         headers = {'content-type': 'application/x-www-form-urlencoded'}
#         request, response = app.test_client.post(
#             '/user/',
#             data=urlencode(data),
#             headers=headers
#         )
#         fake_render.assert_called_with(
#             'user-form.html',
#             ANY,
#             form=ANY,
#             new=True
#         )


def test_user_page_post_create():
    user_data = {
        'name': 'testname',
        'email': 'test_email1@test.com',
        'phone': '0999999999',
        'mobile': '0999999999',
        'status': '1'
    }
    headers = {'content-type': 'application/x-www-form-urlencoded'}
    request, response = app.test_client.post(
        '/user/',
        data=urlencode(user_data),
        headers=headers,
        allow_redirects=False
    )

    # Check redirect.
    assert response.status == 302
    assert response.headers["Location"] == "/"
    assert response.headers["Content-Type"] == 'text/html; charset=utf-8'

    # Check if user was created.
    assert User.select().where(
        User.name == user_data['name'],
        User.email == user_data['email'],
        User.phone == user_data['phone'],
        User.mobile == user_data['mobile'],
        User.status == user_data['status']
    ).exists()


def test_user_page_post_edit():
    user_data = {
        'name': 'testname',
        'email': 'test_email_21@test.com',
        'phone': '0999999992',
        'mobile': '0999999992',
        'status': '0'
    }
    headers = {'content-type': 'application/x-www-form-urlencoded'}
    request, response = app.test_client.post(
        '/user/2',
        data=urlencode(user_data),
        headers=headers,
        allow_redirects=False
    )

    # Check redirect.
    assert response.status == 302
    assert response.headers["Location"] == "/"
    assert response.headers["Content-Type"] == 'text/html; charset=utf-8'

    # Check if user was created.
    assert User.select().where(
        User.name == user_data['name'],
        User.email == user_data['email'],
        User.phone == user_data['phone'],
        User.mobile == user_data['mobile'],
        User.status == user_data['status']
    ).exists()


def test_user_page_delete():
    request, response = app.test_client.get('/user/2')
    assert response.status == 200

    # Delete the user.
    request, response = app.test_client.delete('/user/2')
    assert response.status == 200

    # The user shouldn't exist.
    request, response = app.test_client.get('/user/2')
    assert response.status == 404


def test_user_page_1():
    request, response = app.test_client.get('/user/1')
    assert response.status == 200


def test_user_page_2():
    request, response = app.test_client.get('/user/3')
    assert response.status == 404
