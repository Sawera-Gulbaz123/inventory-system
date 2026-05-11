# backend/routes/auth.py
# Handles login and getting current user info

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta

import models, schemas
from database import get_db
from auth_utils import (
    verify_password, create_access_token,
    get_current_user, ACCESS_TOKEN_EXPIRE_MINUTES,
    log_activity
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ── LOGIN ────────────────────────────────────────────────────────
# OAuth2PasswordRequestForm automatically reads
# username and password from the request body
@router.post("/login", response_model=schemas.Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db:        Session = Depends(get_db)
):
    # Find user by username
    user = db.query(models.User).filter(
        models.User.username == form_data.username
    ).first()

    # Check user exists and password is correct
    # We check both in one condition to prevent
    # timing attacks (where response time reveals if user exists)
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check account is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is disabled"
        )

    # Create JWT token
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    # Log the login action
    log_activity(db, user.id, "Login", f"{user.username} logged in")

    return {
        "access_token": access_token,
        "token_type":   "bearer",
        "role":         user.role,
        "username":     user.username,
    }


# ── GET CURRENT USER ─────────────────────────────────────────────
@router.get("/me", response_model=schemas.UserResponse)
def get_me(current_user: models.User = Depends(get_current_user)):
    """
    Returns the currently logged in user's info.
    Frontend calls this on app load to verify token is still valid.
    """
    return current_user


# ── LOGOUT ───────────────────────────────────────────────────────
@router.post("/logout")
def logout(
    current_user: models.User = Depends(get_current_user),
    db:           Session = Depends(get_db)
):
    """
    JWT tokens cannot be truly invalidated server-side
    without a token blacklist. For a local single-user
    app, logging the logout and having the frontend
    delete the token is sufficient.
    """
    log_activity(db, current_user.id, "Logout", f"{current_user.username} logged out")
    return {"message": "Logged out successfully"}