# backend/routes/users.py
# User management — admin only

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

import models, schemas
from database import get_db
from auth_utils import hash_password, require_admin, get_current_user, log_activity

router = APIRouter(prefix="/users", tags=["Users"])


# ── GET ALL USERS (admin only) ───────────────────────────────────
@router.get("/", response_model=List[schemas.UserResponse])
def get_users(
    db:           Session     = Depends(get_db),
    current_user: models.User = Depends(require_admin)
):
    return db.query(models.User).all()


# ── CREATE USER (admin only) ─────────────────────────────────────
@router.post("/", response_model=schemas.UserResponse)
def create_user(
    user:         schemas.UserCreate,
    db:           Session     = Depends(get_db),
    current_user: models.User = Depends(require_admin)
):
    # Check username is not taken
    existing = db.query(models.User).filter(
        models.User.username == user.username
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")

    # Hash the password before saving
    new_user = models.User(
        username  = user.username,
        password  = hash_password(user.password),
        role      = user.role,
        is_active = True,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    log_activity(
        db, current_user.id,
        "Created User",
        f"Created user '{user.username}' with role '{user.role}'"
    )

    return new_user


# ── UPDATE USER (admin only) ─────────────────────────────────────
@router.put("/{user_id}", response_model=schemas.UserResponse)
def update_user(
    user_id:      int,
    user:         schemas.UserUpdate,
    db:           Session     = Depends(get_db),
    current_user: models.User = Depends(require_admin)
):
    existing = db.query(models.User).filter(
        models.User.id == user_id
    ).first()

    if not existing:
        raise HTTPException(status_code=404, detail="User not found")

    # Update only provided fields
    if user.username is not None:
        existing.username = user.username
    if user.password is not None:
        existing.password = hash_password(user.password)
    if user.role is not None:
        existing.role = user.role
    if user.is_active is not None:
        existing.is_active = user.is_active

    db.commit()
    db.refresh(existing)

    log_activity(
        db, current_user.id,
        "Updated User",
        f"Updated user '{existing.username}'"
    )

    return existing


# ── DELETE USER (admin only) ─────────────────────────────────────
@router.delete("/{user_id}")
def delete_user(
    user_id:      int,
    db:           Session     = Depends(get_db),
    current_user: models.User = Depends(require_admin)
):
    # Prevent admin from deleting themselves
    if user_id == current_user.id:
        raise HTTPException(
            status_code=400,
            detail="You cannot delete your own account"
        )

    user = db.query(models.User).filter(
        models.User.id == user_id
    ).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    username = user.username
    db.delete(user)
    db.commit()

    log_activity(
        db, current_user.id,
        "Deleted User",
        f"Deleted user '{username}'"
    )

    return {"message": f"User '{username}' deleted"}


# ── GET ACTIVITY LOGS (admin only) ───────────────────────────────
@router.get("/activity-logs", response_model=List[schemas.ActivityLogResponse])
def get_activity_logs(
    db:           Session     = Depends(get_db),
    current_user: models.User = Depends(require_admin)
):
    return db.query(models.ActivityLog).order_by(
        models.ActivityLog.timestamp.desc()
    ).limit(200).all()