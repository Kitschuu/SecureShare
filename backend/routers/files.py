import os
import base64
import hashlib
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List

import models
import schemas
from database import get_db
from routers.auth import get_current_user

router = APIRouter(tags=["files"])

UPLOAD_DIR = "uploads"
# Ensure the uploads directory exists on the server
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.get("/users", response_model=List[schemas.PublicKeyResponse])
def get_public_key_directory(db: Session = Depends(get_db)):
    """Return a list of all registered users and their public keys."""
    users = db.query(models.User).all()
    return users

@router.post("/files/share")
async def share_file(
    receiver_id: int = Form(...),
    encrypted_aes_key: str = Form(...),
    digital_signature: str = Form(...),
    filename: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Uploads an encrypted file and routes it to the receiver."""
    # Verify receiver exists
    receiver = db.query(models.User).filter(models.User.id == receiver_id).first()
    if not receiver:
        raise HTTPException(status_code=404, detail="Receiver not found")

    # Save the encrypted file to the local file system securely
    file_path = os.path.join(UPLOAD_DIR, f"{current_user.id}_{receiver_id}_{file.filename}")
    file_bytes = await file.read()
    with open(file_path, "wb") as buffer:
        buffer.write(file_bytes)

    # Server-side integrity hash of the encrypted file
    physical_hash = hashlib.sha256(file_bytes).hexdigest()

    # Create file record
    new_file = models.File(
        filename=filename,
        owner_id=current_user.id,
        encrypted_path=file_path,
        file_hash=physical_hash,
        digital_signature=digital_signature
    )
    db.add(new_file)
    db.commit()
    db.refresh(new_file)

    # Create share record
    new_share = models.Share(
        file_id=new_file.id,
        sender_id=current_user.id,
        receiver_id=receiver.id,
        encrypted_key=encrypted_aes_key
    )
    db.add(new_share)
    db.commit()

    # Log the action for auditing
    log = models.Log(user_id=current_user.id, action="Upload & Share")
    db.add(log)
    db.commit()

    return {"message": "File shared successfully", "file_id": new_file.id}

@router.get("/files/shared", response_model=List[schemas.SharedFileResponse])
def get_shared_files(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """Return a list of files shared with the current authenticated user."""
    shares = db.query(models.Share).filter(models.Share.receiver_id == current_user.id).all()
    result = []
    for share in shares:
        file_record = db.query(models.File).filter(models.File.id == share.file_id).first()
        sender_record = db.query(models.User).filter(models.User.id == share.sender_id).first()
        if file_record and sender_record:
            result.append({
                "share_id": share.id,
                "file_id": file_record.id,
                "filename": file_record.filename,
                "sender_username": sender_record.username
            })
    return result

@router.get("/files/download/{share_id}", response_model=schemas.DownloadPayload)
def download_shared_file(share_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """Retrieve the complete payload needed for Streamlit to decrypt the file locally."""
    # Validate receiver authorization
    share = db.query(models.Share).filter(models.Share.id == share_id).first()
    if not share:
        raise HTTPException(status_code=404, detail="Share record not found")
    if share.receiver_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to download this file")

    file_record = db.query(models.File).filter(models.File.id == share.file_id).first()
    sender_record = db.query(models.User).filter(models.User.id == share.sender_id).first()

    if not file_record or not sender_record:
        raise HTTPException(status_code=404, detail="File or sender not found")

    # Read the encrypted file bytes from the backend file system
    try:
        with open(file_record.encrypted_path, "rb") as f:
            file_bytes = f.read()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Encrypted file not found on server")

    # Encode bytes to Base64 to transmit cleanly via JSON
    encoded_file = base64.b64encode(file_bytes).decode("utf-8")

    # Log the action for auditing
    log = models.Log(user_id=current_user.id, action="Download")
    db.add(log)
    db.commit()

    return {
        "filename": file_record.filename,
        "encrypted_file_blob": encoded_file,
        "encrypted_aes_key": share.encrypted_key,
        "digital_signature": file_record.digital_signature, 
        "sender_public_key": sender_record.public_key
    }
