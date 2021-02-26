from urllib.parse import urlencode

from tests.conftest import app


# Tests.
def test_home_page(setup):
    _, response = app.test_client.get("/")
    assert response.status == 200

    _, response = app.test_client.get("/?items=10")
    assert response.status == 200

    _, response = app.test_client.get("/?items=20&search=t")
    assert response.status == 200


def test_courses_page(setup):
    _, response = app.test_client.get("/courses")
    assert response.status == 200


def test_about_page(setup):
    _, response = app.test_client.get("/about")
    assert response.status == 200


def test_user_page_get(setup):
    _, response = app.test_client.get("/user/")
    assert response.status == 200


def test_user_page_post_create(setup):
    user_data = {
        "name": "testname",
        "email": "test_email1@test.com",
        "phone": "0999999999",
        "mobile": "0999999999",
        "status": "active",
    }
    headers = {"content-type": "application/x-www-form-urlencoded"}
    _, response = app.test_client.post(
        "/user/", data=urlencode(user_data), headers=headers, allow_redirects=False
    )

    # Check redirect.
    assert response.status == 302
    assert response.headers["Location"] == "/"
    assert response.headers["Content-Type"] == "text/html; charset=utf-8"

    _, response = app.test_client.get("/user/2")
    assert response.status == 200

    _, response = app.test_client.get("/user/3")
    assert response.status == 404


def test_user_page_post_edit(setup):
    user_data = {
        "name": "testname",
        "email": "test_email_21@test.com",
        "phone": "0999999992",
        "mobile": "0999999992",
        "status": "inactive",
    }
    headers = {"content-type": "application/x-www-form-urlencoded"}
    _, response = app.test_client.post(
        "/user/1", data=urlencode(user_data), headers=headers, allow_redirects=False
    )

    # Check redirect.
    assert response.status == 302
    assert response.headers["Location"] == "/"
    assert response.headers["Content-Type"] == "text/html; charset=utf-8"


def test_user_page_delete(setup):
    _, response = app.test_client.get("/user/1")
    assert response.status == 200

    # Delete the user.
    _, response = app.test_client.delete("/user/1")
    assert response.status == 200

    # The user shouldn't exist.
    _, response = app.test_client.get("/user/1")
    assert response.status == 404
