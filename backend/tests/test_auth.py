"""
Tests: Authentication endpoints
/api/auth/register and /api/auth/login
"""

import asyncio

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.database import Base, get_async_db
from app.main import app

# In-memory SQLite for tests 
# The auth routes depend on `get_async_db` (AsyncSession), not the sync
# `get_db` 

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