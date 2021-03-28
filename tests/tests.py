from urllib.parse import urlencode

from tests.conftest import app


# Tests.
def test_home_page(db_setup):
    _, response = app.test_client.get("/")
    assert response.status == 200

    _, response = app.test_client.get("/?items=1")
    assert response.status == 200

    _, response = app.test_client.get("/?items=1&page=2")
    assert response.status == 200

    _, response = app.test_client.get("/?items=10")
    assert response.status == 200

    # default per page is used.
    _, response = app.test_client.get("/?items=invalid")
    assert response.status == 200

    _, response = app.test_client.get("/?items=20&search=t")
    assert response.status == 200


def test_courses_page(db_setup):
    _, response = app.test_client.get("/courses")
    assert response.status == 200


def test_about_page(db_setup):
    _, response = app.test_client.get("/about")
    assert response.status == 200


def test_user_page_get(db_setup):
    _, response = app.test_client.get("/user/")
    assert response.status == 200


def test_user_page_post_create(db_setup):
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

    _, response = app.test_client.get("/user/3")
    assert response.status == 200

    # Try to create an user with same username.
    _, response = app.test_client.post(
        "/user/", data=urlencode(user_data), headers=headers, allow_redirects=False
    )
    assert response.status == 200  # form with error

    _, response = app.test_client.get("/user/4")
    assert response.status == 404


def test_user_page_post_edit(db_setup):
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

    # This user do not exist.
    _, response = app.test_client.post(
        "/user/100", data=urlencode(user_data), headers=headers, allow_redirects=False
    )
    assert response.status == 404


def test_user_page_delete(db_setup):
    _, response = app.test_client.get("/user/1")
    assert response.status == 200

    # Delete the user.
    _, response = app.test_client.delete("/user/1")
    assert response.status == 200

    # The user shouldn't exist.
    _, response = app.test_client.get("/user/1")
    assert response.status == 404

    # Try to delete deleted user.
    _, response = app.test_client.delete("/user/1")
    assert response.status == 404
