from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

# --- USER SCHEMAS ---
class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    public_key: str

    class Config:
        from_attributes = True

class PublicKeyResponse(BaseModel):
    id: int
    username: str
    public_key: str

    class Config:
        from_attributes = True

# --- FILE SCHEMAS ---
class FileBase(BaseModel):
    filename: str

class FileCreate(FileBase):
    encrypted_path: str
    file_hash: str
    digital_signature: str

class FileResponse(FileBase):
    id: int
    owner_id: int
    encrypted_path: str
    file_hash: str
    digital_signature: str

    class Config:
        from_attributes = True

class SharedFileResponse(BaseModel):
    share_id: int
    file_id: int
    filename: str
    sender_username: str

class DownloadPayload(BaseModel):
    filename: str
    encrypted_file_blob: str  # Base64 encoded inside JSON
    encrypted_aes_key: str
    digital_signature: str
    sender_public_key: str

# --- SHARE SCHEMAS ---
class ShareBase(BaseModel):
    file_id: int
    receiver_id: int
    encrypted_key: str

class ShareCreate(ShareBase):
    pass

class ShareResponse(ShareBase):
    id: int
    sender_id: int

    class Config:
        from_attributes = True

# --- LOG SCHEMAS ---
class LogBase(BaseModel):
    action: str

class LogCreate(LogBase):
    user_id: Optional[int] = None

class LogResponse(LogBase):
    id: int
    user_id: Optional[int]
    timestamp: datetime

    class Config:
        from_attributes = True
        
from typing import List
from datetime import datetime

# --- Admin & Dashboard Schemas ---

class IntegrityReport(BaseModel):
    total_files: int
    intact_files: List[str]
    compromised_files: List[str]

class StatsResponse(BaseModel):
    total_users: int
    total_files: int
    total_shares: int
    total_actions: int

class LogResponse(BaseModel):
    id: int
    user_id: int
    action: str
    timestamp: datetime

    class Config:
        from_attributes = True