"""Shared test setup.

The tests run against a throwaway SQLite file, never your real PostgreSQL
database. The environment variables below must be set BEFORE `main` is
imported, because main.py creates its database engine when it loads.
"""

import os

os.environ["DATABASE_URL"] = "sqlite:///./test_finance.db"
os.environ["SECRET_KEY"] = "test-secret-key-for-automated-tests"

import pytest
from fastapi.testclient import TestClient

import main

# Cheaper password hashing so the test suite runs fast.
# (Real hashing in main.py is unchanged.)
main.pwd_context.update(bcrypt__rounds=4)


@pytest.fixture(autouse=True)
def fresh_database():
    """Give every test an empty database."""
    # Safety net: refuse to run if this is not the SQLite test database.
    assert main.engine.url.get_backend_name() == "sqlite", (
        "Tests must never run against the real database"
    )

    main.Base.metadata.drop_all(main.engine)
    main.Base.metadata.create_all(main.engine)

    yield


@pytest.fixture
def client():
    return TestClient(main.app)


@pytest.fixture
def make_user(client):
    """Register a user, log in, and return the auth headers."""

    def _make_user(username="alice", password="secret123"):
        client.post(
            "/register",
            json={"username": username, "password": password},
        )

        response = client.post(
            "/login",
            json={"username": username, "password": password},
        )

        token = response.json()["access_token"]

        return {"Authorization": f"Bearer {token}"}

    return _make_user


@pytest.fixture
def alice(make_user):
    return make_user("alice")


@pytest.fixture
def bob(make_user):
    return make_user("bob")
