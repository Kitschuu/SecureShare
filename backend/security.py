from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
import bcrypt
import hashlib
from Crypto.PublicKey import RSA

# Configuration (In production, load these from environment variables)
SECRET_KEY = "super-secret-key-change-me"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

def get_password_hash(password: str) -> str:
    # Hash with SHA-256 first to avoid bcrypt's 72-byte limit
    sha_hashed = hashlib.sha256(password.encode('utf-8')).hexdigest()
    # Use bcrypt directly without going through passlib (which crashes on verify wrap bug test)
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(sha_hashed.encode('utf-8'), salt).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        sha_hashed = hashlib.sha256(plain_password.encode('utf-8')).hexdigest()
        return bcrypt.checkpw(sha_hashed.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def generate_rsa_key_pair():
    """Generates a 2048-bit RSA key pair."""
    key = RSA.generate(2048)
    private_key = key.export_key().decode('utf-8')
    public_key = key.publickey().export_key().decode('utf-8')
    return private_key, public_key
