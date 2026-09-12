from uuid import uuid4


def test_register_user(client):
    email = f"ada-{uuid4()}@example.com"
    response = client.post(
        "/api/v1/users",
        json={
            "name": "Ada Lovelace",
            "email": email,
            "password": "correct-horse-battery-staple",
        },
    )

    assert response.status_code == 201
    assert response.json()["email"] == email
    assert "password" not in response.json()


def test_cannot_register_duplicate_email(client):
    email = f"ada-{uuid4()}@example.com"
    payload = {
        "name": "Ada Lovelace",
        "email": email,
        "password": "correct-horse-battery-staple",
    }
    assert client.post("/api/v1/users", json=payload).status_code == 201

    response = client.post("/api/v1/users", json=payload)

    assert response.status_code == 409
