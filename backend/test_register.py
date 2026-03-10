import sys
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import models

logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

from database import engine, SessionLocal
import security

try:
    db = SessionLocal()
    
    hashed_password = security.get_password_hash("test12345")
    private_key, public_key = security.generate_rsa_key_pair()
    
    new_user = models.User(
        username="testuser999",
        email="testuser999@example.com",
        password_hash=hashed_password,
        public_key=public_key
    )
    db.add(new_user)
    db.commit()
    print("Success")
except Exception as e:
    print("ERROR:")
    import traceback
    traceback.print_exc()
