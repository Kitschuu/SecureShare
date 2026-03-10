import hashlib
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
import models, schemas
from routers.auth import get_current_user

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/integrity-check", response_model=schemas.IntegrityReport)
def integrity_check(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """Comprehensive integrity check of all files stored on the server."""
    files = db.query(models.File).all()
    total_files = len(files)
    intact_files = []
    compromised_files = []
    
    for f in files:
        try:
            with open(f.encrypted_path, "rb") as physical_file:
                file_bytes = physical_file.read()
                physical_hash = hashlib.sha256(file_bytes).hexdigest()
                
                if physical_hash == f.file_hash:
                    intact_files.append(f.filename)
                else:
                    compromised_files.append(f"{f.filename} (Hash mismatch)")
        except FileNotFoundError:
            compromised_files.append(f"{f.filename} (File missing)")

    # Log action
    log = models.Log(user_id=current_user.id, action="System Integrity Scan")
    db.add(log)
    db.commit()

    return {
        "total_files": total_files,
        "intact_files": intact_files,
        "compromised_files": compromised_files
    }

@router.get("/logs", response_model=List[schemas.LogResponse])
def get_logs(limit: int = 50, offset: int = 0, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """Retrieve the latest security events."""
    logs = db.query(models.Log).order_by(models.Log.timestamp.desc()).offset(offset).limit(limit).all()
    return logs

@router.get("/stats", response_model=schemas.StatsResponse)
def get_stats(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """Aggregated statistics for the Security Dashboard."""
    total_users = db.query(models.User).count()
    total_files = db.query(models.File).count()
    total_shares = db.query(models.Share).count()
    total_actions = db.query(models.Log).count()
    
    return {
        "total_users": total_users,
        "total_files": total_files,
        "total_shares": total_shares,
        "total_actions": total_actions
    }
