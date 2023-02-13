# End-to-End Tests
from fastapi.testclient import TestClient
import main

client = TestClient(main.app)


def user_authentication_headers(username: str, password: str):
    login_data = {'username': username, 'password': password}
    r = client.post('/token/', data=login_data,
                    headers={'Content-Type': 'application/x-www-form-urlencoded'})
    response = r.json()
    auth_token = response["access_token"]
    headers = {"Authorization": f"Bearer {auth_token}"}
    return headers


def test_login_with_correct_password():
    username = 'admin'
    password = 'admin'
    login_data = {'username': username, 'password': password}
    response = client.post('/token/', data=login_data,
                           headers={'Content-Type': 'application/x-www-form-urlencoded'})
    assert response.status_code == 200


def test_login_with_wrong_password():
    username = 'admin'
    password = 'wrongpassword'
    login_data = {'username': username, 'password': password}
    response = client.post('/token/', data=login_data,
                           headers={'Content-Type': 'application/x-www-form-urlencoded'})
    assert response.status_code == 400


def test_create_user():
    header = user_authentication_headers("admin", "admin")
    response = client.post("/users/", json={
        "username": "testuser",
        "full_name": "testuser",
        "email": "testuser@gmail.com",
        "password": "password"
    }, headers=header)
    assert response.status_code == 200
    assert response.json()["username"] == "testuser"
    assert response.json()["email"] == "testuser@gmail.com"


def test_edit_user():
    header = user_authentication_headers("admin", "admin")
    response = client.put("/users/2", json={
        "username": "testuser",
        "full_name": "testuser2",
        "email": "testuser@gmail.com",
        "password": "password"
    }, headers=header)
    assert response.status_code == 200
    assert response.json()["full_name"] == "testuser2"


#
#
def test_create_group():
    header = user_authentication_headers("admin", "admin")
    response = client.post("/groups/", json={
        "name": "testgroup",
        "description": "group description"
    }, headers=header)
    assert response.status_code == 200
    assert response.json()["name"] == "testgroup"


def test_search_group():
    header = user_authentication_headers("admin", "admin")
    response = client.get("/groups/search?name=testgroup", headers=header)
    assert response.status_code == 200
    assert response.json()["groups"][0]["name"] == "testgroup"


def test_add_members():
    header = user_authentication_headers("admin", "admin")

    response = client.post("/groups/1/members?user_id=2", headers=header)
    assert response.status_code == 200
    assert response.json()["user_id"] == 2
    assert response.json()["group_id"] == 1


def test_send_message():
    header = user_authentication_headers("admin", "admin")
    response = client.post("/groups/1/messages/", json={
        "message": "TestMessage"
    }, headers=header)
    assert response.status_code == 200
    assert response.json()["message"] == "TestMessage"
    assert response.json()["group_id"] == 1

def test_like_message():
    header = user_authentication_headers("admin", "admin")
    response = client.post("/groups/1/messages/1/likes/", headers=header)
    assert response.status_code == 200
    assert response.json()["message_id"] == 1

def test_delete_group():
    header = user_authentication_headers("admin", "admin")
    response = client.delete("/groups/1", headers=header)
    assert response.status_code == 200
    assert response.json() == {"message": "Group deleted"}






















