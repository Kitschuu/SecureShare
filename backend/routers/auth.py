from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from jose import JWTError, jwt

import models
import schemas
from database import get_db
from security import (
    verify_password,
    get_password_hash,
    create_access_token,
    generate_rsa_key_pair,
    SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)

router = APIRouter(prefix="/auth", tags=["auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Dependency to retrieve the current authenticated user via JWT."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(models.User).filter(models.User.username == username).first()
    if user is None:
        raise credentials_exception
    return user

@router.post("/register", status_code=status.HTTP_201_CREATED)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """Registers a new user, generating an RSA key pair."""
    # Check if user exists
    db_user = db.query(models.User).filter(
        (models.User.username == user.username) | (models.User.email == user.email)
    ).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username or email already registered")
    
    # Hash the password
    hashed_password = get_password_hash(user.password)
    
    # Generate 2048-bit RSA keys
    private_key, public_key = generate_rsa_key_pair()
    
    # Create new user record (ONLY store the public key)
    new_user = models.User(
        username=user.username,
        email=user.email,
        password_hash=hashed_password,
        public_key=public_key
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Log the action (Audit Logging)
    log = models.Log(user_id=new_user.id, action="Register")
    db.add(log)
    db.commit()
    
    # We return the private key in the response exactly ONCE.
    # It must NEVER be stored on the server side.
    return {
        "message": "User registered successfully.",
        "user_id": new_user.id,
        "username": new_user.username,
        "private_key": private_key,
        "instructions": "SAVE THIS PRIVATE KEY NOW. The server does not store it. You will need it to decrypt files and sign messages."
    }

@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Authenticates the user and returns a JWT token."""
    # Find user by username
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Generate JWT access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    # Log the action (Audit Logging)
    log = models.Log(user_id=user.id, action="Login")
    db.add(log)
    db.commit()
    
    return {"access_token": access_token, "token_type": "bearer"}
