from uuid import uuid4


def create_user(client):
    email = f"grace-{uuid4()}@example.com"
    return client.post(
        "/api/v1/users",
        json={
            "name": "Grace Hopper",
            "email": email,
            "password": "correct-horse-battery-staple",
        },
    )


def test_login_returns_bearer_token(client):
    user = create_user(client)
    assert user.status_code == 201

    response = client.post(
        "/api/v1/auth/login",
        json={"email": user.json()["email"], "password": "correct-horse-battery-staple"},
    )

    assert response.status_code == 200
    assert response.json()["tokenType"] == "bearer"
    assert response.json()["accessToken"]


def test_login_rejects_invalid_password(client):
    user = create_user(client)
    assert user.status_code == 201

    response = client.post(
        "/api/v1/auth/login",
        json={"email": user.json()["email"], "password": "incorrect"},
    )

    assert response.status_code == 401
