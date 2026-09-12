from uuid import uuid4

import pyotp

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


def authenticated_headers(client):
    user = create_user(client)
    token = client.post(
        "/api/v1/auth/login",
        data={"username": user.json()["email"], "password": "correct-horse-battery-staple"},
    ).json()["accessToken"]
    return user.json(), {"Authorization": f"Bearer {token}"}


def test_login_returns_bearer_token(client):
    user = create_user(client)
    assert user.status_code == 201

    response = client.post(
        "/api/v1/auth/login",
        data={"username": user.json()["email"], "password": "correct-horse-battery-staple"},
    )

    assert response.status_code == 200
    assert response.json()["tokenType"] == "bearer"
    assert response.json()["accessToken"]


def test_login_rejects_invalid_password(client):
    user = create_user(client)
    assert user.status_code == 201

    response = client.post(
        "/api/v1/auth/login",
        data={"username": user.json()["email"], "password": "incorrect"},
    )

    assert response.status_code == 401


def test_authenticated_profile_and_password_verification(client):
    user, headers = authenticated_headers(client)

    profile = client.get("/api/v1/auth/me", headers=headers)
    verified = client.post(
        "/api/v1/auth/verify-by-password",
        headers=headers,
        json={"password": "correct-horse-battery-staple"},
    )
    invalid = client.post(
        "/api/v1/auth/verify-by-password",
        headers=headers,
        json={"password": "incorrect"},
    )
    updated = client.put(
        "/api/v1/auth/me",
        headers=headers,
        json={"name": "Grace Murray Hopper", "email": user["email"], "phone": "+15551234567"},
    )

    assert profile.status_code == 200
    assert profile.json()["email"] == user["email"]
    assert verified.status_code == 200
    assert verified.json() is True
    assert invalid.status_code == 400
    assert updated.status_code == 200
    assert updated.json()["name"] == "Grace Murray Hopper"


def test_change_password_invalidates_old_credentials(client):
    user, headers = authenticated_headers(client)

    changed = client.put(
        "/api/v1/auth/change-password",
        headers=headers,
        json={
            "currentPassword": "correct-horse-battery-staple",
            "newPassword": "new-correct-horse-battery-staple",
        },
    )
    old_login = client.post(
        "/api/v1/auth/login",
        data={"username": user["email"], "password": "correct-horse-battery-staple"},
    )
    new_login = client.post(
        "/api/v1/auth/login",
        data={"username": user["email"], "password": "new-correct-horse-battery-staple"},
    )

    assert changed.status_code == 200
    assert old_login.status_code == 401
    assert new_login.status_code == 200


def test_password_reset_sends_email_and_accepts_reset_token(client, monkeypatch):
    user = create_user(client).json()
    delivered: dict = {}

    async def send_email_mock(self, **kwargs):
        delivered.update(kwargs)

    monkeypatch.setattr(
        "app.infraestructure.email.email_sender.EmailSender.send_email", send_email_mock
    )
    requested = client.post("/api/v1/auth/forgot-password", json={"email": user["email"]})
    token = delivered["context"]["reset_url"].rsplit("token=", 1)[1]
    reset = client.post(
        "/api/v1/auth/reset-password",
        json={"token": token, "newPassword": "reset-correct-horse-battery-staple"},
    )
    login = client.post(
        "/api/v1/auth/login",
        data={"username": user["email"], "password": "reset-correct-horse-battery-staple"},
    )

    assert requested.status_code == 200
    assert delivered["email_to"] == user["email"]
    assert reset.status_code == 200
    assert login.status_code == 200


def test_mfa_setup_enable_verify_and_disable(client):
    user, headers = authenticated_headers(client)

    setup = client.post("/api/v1/auth/me/setup-2fa", headers=headers)
    secret = setup.json()["otp_secret"]
    code = pyotp.TOTP(secret).now()
    enabled = client.post("/api/v1/auth/enable-2fa", headers=headers, json={"code": code})
    mfa_login = client.post(
        "/api/v1/auth/login",
        data={"username": user["email"], "password": "correct-horse-battery-staple"},
    )
    mfa_token = mfa_login.json()["accessToken"]
    verified = client.post(
        f"/api/v1/auth/verify-2fa/{pyotp.TOTP(secret).now()}",
        headers={"Authorization": f"Bearer {mfa_token}"},
    )
    access_token = verified.json()["accessToken"]
    disabled = client.post(
        "/api/v1/auth/disable-2fa",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert setup.status_code == 200
    assert enabled.status_code == 200
    assert mfa_login.status_code == 200
    assert mfa_login.json()["tokenRole"] == "mfa"
    assert verified.status_code == 200
    assert disabled.status_code == 200
