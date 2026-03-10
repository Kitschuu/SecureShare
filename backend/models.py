from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    public_key = Column(String, nullable=False)  # PEM format RSA public key
    
    # Relationships
    files_owned = relationship("File", back_populates="owner", cascade="all, delete-orphan")
    shares_sent = relationship("Share", foreign_keys="[Share.sender_id]", back_populates="sender")
    shares_received = relationship("Share", foreign_keys="[Share.receiver_id]", back_populates="receiver")
    logs = relationship("Log", back_populates="user")


class File(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    encrypted_path = Column(String, nullable=False)
    file_hash = Column(String, nullable=False)  # SHA-256 Hash for integrity
    digital_signature = Column(String, nullable=False)  # RSA signature
    
    owner = relationship("User", back_populates="files_owned")
    shares = relationship("Share", back_populates="file", cascade="all, delete-orphan")


class Share(Base):
    __tablename__ = "shares"

    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey("files.id"), nullable=False)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    receiver_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    # AES key used to encrypt the file, encrypted with receiver's public key
    encrypted_key = Column(String, nullable=False) 
    
    file = relationship("File", back_populates="shares")
    sender = relationship("User", foreign_keys=[sender_id], back_populates="shares_sent")
    receiver = relationship("User", foreign_keys=[receiver_id], back_populates="shares_received")


class Log(Base):
    __tablename__ = "logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Nullable for unauth actions
    action = Column(String, nullable=False)  # Login, Upload, Download, Share, Verify
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="logs")
