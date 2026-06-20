"""
Tests: Authentication endpoints
/api/auth/register and /api/auth/login
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app

# ── In-memory SQLite for tests ────────────────────────────────────────────────

TEST_DB_URL = "sqlite:///./test_vestora.db"

engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestSession()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = override_get_db
    yield
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestRegister:
    def test_register_success(self, client):
        res = client.post("/api/auth/register", json={
            "email": "test@vestora.africa",
            "password": "securepass123",
            "full_name": "Test User",
        })
        assert res.status_code == 201
        data = res.json()
        assert data["email"] == "test@vestora.africa"
        assert data["tier"] == "free"
        assert "id" in data

    def test_register_duplicate_email(self, client):
        payload = {"email": "dupe@vestora.africa", "password": "pass123"}
        client.post("/api/auth/register", json=payload)
        res = client.post("/api/auth/register", json=payload)
        assert res.status_code == 400
        assert "already registered" in res.json()["detail"]

    def test_register_missing_email(self, client):
        res = client.post("/api/auth/register", json={"password": "pass123"})
        assert res.status_code == 422


class TestLogin:
    def test_login_success(self, client):
        client.post("/api/auth/register", json={
            "email": "login@vestora.africa",
            "password": "mypassword",
        })
        res = client.post("/api/auth/login", data={
            "username": "login@vestora.africa",
            "password": "mypassword",
        })
        assert res.status_code == 200
        data = res.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client):
        client.post("/api/auth/register", json={
            "email": "wrong@vestora.africa",
            "password": "correctpass",
        })
        res = client.post("/api/auth/login", data={
            "username": "wrong@vestora.africa",
            "password": "wrongpass",
        })
        assert res.status_code == 401

    def test_login_unknown_user(self, client):
        res = client.post("/api/auth/login", data={
            "username": "nobody@vestora.africa",
            "password": "whatever",
        })
        assert res.status_code == 401