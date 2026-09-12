from uuid import uuid4


def authenticated_headers(client):
    email = f"margaret-{uuid4()}@example.com"
    client.post(
        "/api/v1/users",
        json={
            "name": "Margaret Hamilton",
            "email": email,
            "password": "correct-horse-battery-staple",
        },
    )
    token = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": "correct-horse-battery-staple"},
    ).json()["accessToken"]
    return {"Authorization": f"Bearer {token}"}


def test_authenticated_user_can_read_own_session(client):
    headers = authenticated_headers(client)

    response = client.get("/api/v1/user-sessions", headers=headers)

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["revokedAt"] is None


def test_revoked_session_cannot_access_protected_route(client):
    headers = authenticated_headers(client)

    assert client.delete("/api/v1/user-sessions/current", headers=headers).status_code == 204

    response = client.get("/api/v1/users/me", headers=headers)

    assert response.status_code == 401
