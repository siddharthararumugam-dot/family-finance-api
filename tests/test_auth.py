"""Registration, login and protected-route tests."""


def test_home_is_public(client):
    response = client.get("/")

    assert response.status_code == 200


def test_register_success(client):
    response = client.post(
        "/register",
        json={"username": "alice", "password": "secret123"},
    )

    assert response.status_code == 200
    assert response.json()["username"] == "alice"


def test_register_duplicate_username_is_rejected(client):
    body = {"username": "alice", "password": "secret123"}

    client.post("/register", json=body)
    response = client.post("/register", json=body)

    assert response.status_code == 400
    assert response.json()["detail"] == "Username already exists"


def test_register_rejects_short_username(client):
    response = client.post(
        "/register",
        json={"username": "ab", "password": "secret123"},
    )

    assert response.status_code == 422


def test_register_rejects_short_password(client):
    response = client.post(
        "/register",
        json={"username": "alice", "password": "123"},
    )

    assert response.status_code == 422


def test_login_success_returns_token(client):
    client.post(
        "/register",
        json={"username": "alice", "password": "secret123"},
    )

    response = client.post(
        "/login",
        json={"username": "alice", "password": "secret123"},
    )

    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert response.json()["access_token"]


def test_login_wrong_password_is_rejected(client):
    client.post(
        "/register",
        json={"username": "alice", "password": "secret123"},
    )

    response = client.post(
        "/login",
        json={"username": "alice", "password": "wrong-password"},
    )

    assert response.status_code == 401


def test_login_unknown_user_is_rejected(client):
    response = client.post(
        "/login",
        json={"username": "nobody", "password": "secret123"},
    )

    assert response.status_code == 401


def test_password_is_not_stored_as_plain_text(client):
    import main

    client.post(
        "/register",
        json={"username": "alice", "password": "secret123"},
    )

    db = main.SessionLocal()

    try:
        user = db.query(main.UserDB).filter_by(username="alice").first()

        assert user.password_hash != "secret123"
        assert user.password_hash.startswith("$2")  # bcrypt hash
    finally:
        db.close()


def test_protected_routes_need_a_token(client):
    protected = [
        "/expenses",
        "/expenses/total",
        "/expenses/summary",
        "/income",
        "/income/total",
        "/balance",
        "/monthly-summary?year=2026&month=11",
    ]

    for path in protected:
        response = client.get(path)

        assert response.status_code in (401, 403), path


def test_invalid_token_is_rejected(client):
    response = client.get(
        "/expenses",
        headers={"Authorization": "Bearer not-a-real-token"},
    )

    assert response.status_code == 401
