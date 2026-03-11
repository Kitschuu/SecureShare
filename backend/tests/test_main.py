import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import json
import os

# Set fake DATABASE_URL before importing main
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from main import app
from database import Base, get_db

# Mock Database Setup
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

# Fixtures for shared state
@pytest.fixture(scope="module")
def test_user():
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword123"
    }

@pytest.fixture(scope="module")
def admin_user():
    return {
        "username": "adminuser",
        "email": "admin@example.com",
        "password": "adminpassword123",
        "role": "admin"
    }

# --- 1. Auth Tests ---
def test_register_user(test_user):
    response = client.post(
        "/auth/register",
        json=test_user
    )
    assert response.status_code == 201
    assert "message" in response.json()
    assert "private_key" in response.json()

def test_register_admin(admin_user):
    response = client.post(
        "/auth/register",
        json=admin_user
    )
    assert response.status_code == 201
    
    # We need to manually set the role to admin in the DB since the register endpoint defaults to "user"
    db = TestingSessionLocal()
    from models import User
    user = db.query(User).filter(User.username == admin_user["username"]).first()
    user.role = "admin"
    db.commit()
    db.close()

def test_login_success(test_user):
    response = client.post(
        "/auth/login",
        data={"username": test_user["username"], "password": test_user["password"]}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_login_failure(test_user):
    response = client.post(
        "/auth/login",
        data={"username": test_user["username"], "password": "wrongpassword"}
    )
    assert response.status_code == 401

# --- 2. RBAC Tests ---
def test_admin_stats_access_forbidden(test_user):
    # Login as standard user
    login_response = client.post(
        "/auth/login",
        data={"username": test_user["username"], "password": test_user["password"]}
    )
    token = login_response.json()["access_token"]
    
    # Attempt to access admin stats
    response = client.get(
        "/admin/stats",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403

def test_admin_stats_access_success(admin_user):
    # Login as admin user
    login_response = client.post(
        "/auth/login",
        data={"username": admin_user["username"], "password": admin_user["password"]}
    )
    token = login_response.json()["access_token"]
    
    # Attempt to access admin stats
    response = client.get(
        "/admin/stats",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert "total_users" in response.json()

# --- 3. File Sharing Tests ---
def test_file_upload(test_user, admin_user):
    # Ensure users exist before trying to log in
    client.post("/auth/register", json=test_user)
    client.post("/auth/register", json=admin_user)
    
    # Login as standard user to send
    login_response = client.post(
        "/auth/login",
        data={"username": test_user["username"], "password": test_user["password"]}
    )
    token = login_response.json()["access_token"]
    
    # Get the admin's user ID to act as receiver
    users_response = client.get(
        "/users",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert users_response.status_code == 200
    users = users_response.json()
    receiver_id = next(u["id"] for u in users if u["username"] == admin_user["username"])
    
    # Prepare dummy file data
    file_data = b"dummy_encrypted_content"
    data = {
        "receiver_id": receiver_id,
        "encrypted_aes_key": "dummy_aes_b64",
        "digital_signature": "dummy_sig_b64",
        "filename": "test_file.txt"
    }
    
    files = {"file": ("test_file.txt", file_data, "application/octet-stream")}
    
    response = client.post(
        "/files/share",
        headers={"Authorization": f"Bearer {token}"},
        data=data,
        files=files
    )
    assert response.status_code == 200
    assert response.json()["message"] == "File shared successfully"

def test_get_shared_files(admin_user):
    # Login as admin user to receive
    login_response = client.post(
        "/auth/login",
        data={"username": admin_user["username"], "password": admin_user["password"]}
    )
    token = login_response.json()["access_token"]
    
    response = client.get(
        "/files/shared",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    shared_files = response.json()
    assert len(shared_files) > 0
    assert shared_files[0]["filename"] == "test_file.txt"
