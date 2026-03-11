import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import json
import os
import base64
from Crypto.PublicKey import RSA
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256
from Crypto.Random import get_random_bytes

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

# -------------------------------------------------------------
# Fixtures for shared state
# -------------------------------------------------------------
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


# -------------------------------------------------------------
# Cryptography Utilities (used for tests)
# -------------------------------------------------------------
def generate_rsa_keys():
    key = RSA.generate(2048)
    private_key = key.export_key()
    public_key = key.publickey().export_key()
    return private_key, public_key

def hybrid_encrypt(data: bytes, public_key_pem: bytes):
    aes_key = get_random_bytes(32) # AES-256
    cipher_aes = AES.new(aes_key, AES.MODE_EAX)
    ciphertext, tag = cipher_aes.encrypt_and_digest(data)
    
    recipient_key = RSA.import_key(public_key_pem)
    cipher_rsa = PKCS1_OAEP.new(recipient_key)
    enc_aes_key = cipher_rsa.encrypt(aes_key)
    
    return {
        "enc_aes_key": base64.b64encode(enc_aes_key).decode('utf-8'),
        "nonce": base64.b64encode(cipher_aes.nonce).decode('utf-8'),
        "tag": base64.b64encode(tag).decode('utf-8'),
        "ciphertext": base64.b64encode(ciphertext).decode('utf-8')
    }

def hybrid_decrypt(encrypted_data: dict, private_key_pem: bytes):
    enc_aes_key = base64.b64decode(encrypted_data["enc_aes_key"])
    nonce = base64.b64decode(encrypted_data["nonce"])
    tag = base64.b64decode(encrypted_data["tag"])
    ciphertext = base64.b64decode(encrypted_data["ciphertext"])
    
    private_key = RSA.import_key(private_key_pem)
    cipher_rsa = PKCS1_OAEP.new(private_key)
    
    try:
        aes_key = cipher_rsa.decrypt(enc_aes_key)
    except ValueError:
        raise ValueError("Decryption failed: wrong private key or corrupted key.")
    
    cipher_aes = AES.new(aes_key, AES.MODE_EAX, nonce=nonce)
    try:
        data = cipher_aes.decrypt_and_verify(ciphertext, tag)
        return data
    except ValueError:
        raise ValueError("Decryption failed: corrupted data.")

def sign_data(data: bytes, private_key_pem: bytes):
    private_key = RSA.import_key(private_key_pem)
    h = SHA256.new(data)
    signature = pkcs1_15.new(private_key).sign(h)
    return base64.b64encode(signature).decode('utf-8')

def verify_signature(data: bytes, signature_b64: str, public_key_pem: bytes):
    public_key = RSA.import_key(public_key_pem)
    h = SHA256.new(data)
    signature = base64.b64decode(signature_b64)
    try:
        pkcs1_15.new(public_key).verify(h, signature)
        return True
    except (ValueError, TypeError):
        raise ValueError("Invalid signature")


# -------------------------------------------------------------
# 1. Authentication Tests
# -------------------------------------------------------------
def test_register_success(test_user):
    response = client.post("/auth/register", json=test_user)
    assert response.status_code == 201
    data = response.json()
    assert "private_key" in data
    assert "user_id" in data
    # Store the private key for later use in tests
    test_user["private_key"] = data["private_key"].encode('utf-8')

def test_register_duplicate(test_user):
    # เลือกลงทะเบียนซ้ำด้วยข้อมูลพื้นฐาน (ไม่รวม private_key ที่อาจจะติดมาเป็น bytes)
    payload = {
        "username": test_user["username"],
        "email": test_user["email"],
        "password": test_user["password"]
    }
    # Attempting to register the same user again should fail
    response = client.post("/auth/register", json=payload)
    
    # ควรจะได้ Error 400 (Bad Request) หรือ 409 (Conflict) กลับมา
    assert response.status_code in [400, 409]

def test_login_success(test_user):
    response = client.post(
        "/auth/login",
        data={"username": test_user["username"], "password": test_user["password"]}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_login_wrong_password(test_user):
    response = client.post(
        "/auth/login",
        data={"username": test_user["username"], "password": "wrongpassword_123"}
    )
    assert response.status_code == 401
    assert "Incorrect username or password" in response.json()["detail"]

def test_login_nonexistent_user():
    response = client.post(
        "/auth/login",
        data={"username": "ghost_user", "password": "ghostpassword_123"}
    )
    assert response.status_code == 401
    assert "Incorrect username or password" in response.json()["detail"]


# -------------------------------------------------------------
# 2. RBAC Tests
# -------------------------------------------------------------
def test_admin_can_access_stats(admin_user):
    # Register Admin
    reg_response = client.post("/auth/register", json=admin_user)
    assert reg_response.status_code == 201

    # In our backend code, users are created with role "user" unless specified in DB directly.
    # The models/schemas default to "user". We need to modify admin_user role to admin in DB mock.
    db = TestingSessionLocal()
    from models import User
    user = db.query(User).filter(User.username == admin_user["username"]).first()
    user.role = "admin"
    db.commit()
    db.close()

    # Login Admin
    login_response = client.post(
        "/auth/login",
        data={"username": admin_user["username"], "password": admin_user["password"]}
    )
    token = login_response.json()["access_token"]
    
    # Access Admin endpoint
    response = client.get(
        "/admin/stats",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert "total_users" in response.json()

def test_regular_user_blocked(test_user):
    # Login as standard user
    login_response = client.post(
        "/auth/login",
        data={"username": test_user["username"], "password": test_user["password"]}
    )
    token = login_response.json()["access_token"]
    
    # Attempt to access admin endpoint
    response = client.get(
        "/admin/stats",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403
    assert "permission" in response.json()["detail"].lower()


# -------------------------------------------------------------
# 3. Cryptography & Security Tests
# -------------------------------------------------------------
def test_encrypt_and_decrypt():
    # 8. Encrypting and then decrypting data should result in an exact data match.
    private_key_pem, public_key_pem = generate_rsa_keys()
    original_data = b"Secret Medical Records - Top Secret"
    
    encrypted = hybrid_encrypt(original_data, public_key_pem)
    decrypted = hybrid_decrypt(encrypted, private_key_pem)
    
    assert decrypted == original_data

def test_signature_valid():
    # 9. Verifying a valid, untampered digital signature should pass.
    private_key_pem, public_key_pem = generate_rsa_keys()
    data = b"Important Document Content"
    
    signature = sign_data(data, private_key_pem)
    # Should not raise any ValueError
    assert verify_signature(data, signature, public_key_pem) is True

def test_signature_tampered():
    # 10. Verifying a tampered file/signature should raise a ValueError.
    private_key_pem, public_key_pem = generate_rsa_keys()
    original_data = b"Important Document Content"
    tampered_data = b"Important Document Content - MODIFIED"
    
    signature = sign_data(original_data, private_key_pem)
    
    with pytest.raises(ValueError, match="Invalid signature"):
        verify_signature(tampered_data, signature, public_key_pem)

def test_signature_wrong_key():
    # 11. Verifying a signature with the wrong public key should fail.
    priv_key1, pub_key1 = generate_rsa_keys()
    priv_key2, pub_key2 = generate_rsa_keys()
    
    data = b"Some data"
    signature = sign_data(data, priv_key1)
    
    # Trying to verify with pub_key2 should fail
    with pytest.raises(ValueError, match="Invalid signature"):
        verify_signature(data, signature, pub_key2)

def test_decrypt_wrong_key():
    # 12. Decrypting with the wrong private key should fail/raise ValueError.
    priv_key_correct, pub_key_correct = generate_rsa_keys()
    priv_key_wrong, pub_key_wrong = generate_rsa_keys()
    
    original_data = b"Data only meant for correct recipient"
    encrypted = hybrid_encrypt(original_data, pub_key_correct)
    
    # Trying to decrypt with the wrong private key
    with pytest.raises(ValueError, match="Decryption failed"):
        hybrid_decrypt(encrypted, priv_key_wrong)

def test_admin_integrity_check(test_user, admin_user):
    # 13. Admin triggering an integrity scan (/admin/integrity-check) should return 200 and a report.
    # First, let's share a file so there is something to scan.
    
    # Login sender (test_user)
    login_response = client.post(
        "/auth/login",
        data={"username": test_user["username"], "password": test_user["password"]}
    )
    sender_token = login_response.json()["access_token"]
    
    # Send a file
    db = TestingSessionLocal()
    from models import User
    admin = db.query(User).filter(User.username == admin_user["username"]).first()
    receiver_id = admin.id
    db.close()
    
    file_content = b"Some file content to test integrity"
    data = {
        "receiver_id": receiver_id,
        "encrypted_aes_key": "dummy_aes_key_b64",
        "digital_signature": "dummy_signature_b64",
        "filename": "integrity_test_file.txt"
    }
    
    files = {"file": ("integrity_test_file.txt", file_content, "application/octet-stream")}
    client.post(
        "/files/share",
        headers={"Authorization": f"Bearer {sender_token}"},
        data=data,
        files=files
    )
    
    # Login admin
    admin_login = client.post(
        "/auth/login",
        data={"username": admin_user["username"], "password": admin_user["password"]}
    )
    admin_token = admin_login.json()["access_token"]
    
    # Trigger Integrity Scan
    response = client.get(
        "/admin/integrity-check",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    assert response.status_code == 200
    report = response.json()
    assert "total_files" in report
    assert "intact_files" in report
    assert "compromised_files" in report
    
    # The uploaded file should be intact
    assert report["total_files"] >= 1
    assert any("integrity_test_file.txt" in f for f in report["intact_files"])
