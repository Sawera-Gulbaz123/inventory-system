# backend/auth_utils.py
# All authentication helper functions live here
# Kept separate from routes to keep things clean

from datetime import datetime, timedelta
from typing import Optional

# JWT = JSON Web Token — a signed token that proves identity
# python-jose handles creating and verifying JWTs
from jose import JWTError, jwt

# passlib handles password hashing with bcrypt
from passlib.context import CryptContext

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from sqlalchemy.orm import Session
from database import get_db
import models

# ── SECRET KEY ──────────────────────────────────────────────────
# This key signs the JWT. Anyone with this key can forge tokens.
# In production this should be a long random string stored in
# an environment variable — never committed to git.
SECRET_KEY  = "ims-super-secret-key-change-in-production-2024"
ALGORITHM   = "HS256"   # Hashing algorithm for the JWT

# Token expires after 30 minutes (session timeout)
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# ── PASSWORD HASHING ────────────────────────────────────────────
# CryptContext manages password hashing
# bcrypt is the industry standard — it is slow by design
# making brute force attacks very difficult
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ── OAUTH2 SCHEME ───────────────────────────────────────────────
# This tells FastAPI where to find the token in requests
# tokenUrl is the login endpoint
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Compares a plain text password against a stored hash.
    Returns True if they match, False otherwise.
    bcrypt handles the comparison securely.
    """
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    """
    Converts a plain text password into a bcrypt hash.
    The hash is what we store in the database.
    e.g. "mypassword" → "$2b$12$KIXs..."
    """
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Creates a signed JWT token.
    data: what to encode inside the token (usually {"sub": username})
    expires_delta: how long until the token expires
    """
    to_encode = data.copy()

    # Set expiry time
    expire = datetime.utcnow() + (
        expires_delta if expires_delta
        else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})

    # Sign and encode the token
    # jwt.encode creates a string like "eyJ0eXAiOiJKV1Qi..."
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db:    Session = Depends(get_db)
) -> models.User:
    """
    Dependency function — FastAPI calls this automatically
    when a route has: current_user = Depends(get_current_user)

    It reads the JWT from the Authorization header,
    decodes it, finds the user in the database,
    and returns the User object.

    If anything is wrong (expired, invalid, user deleted),
    it raises a 401 Unauthorized error.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Decode the JWT — this also checks expiry automatically
        payload  = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        # "sub" (subject) is where we stored the username
        username = payload.get("sub")
        if username is None:
            raise credentials_exception

    except JWTError:
        # Token is invalid or expired
        raise credentials_exception

    # Find the user in the database
    user = db.query(models.User).filter(
        models.User.username == username
    ).first()

    if user is None or not user.is_active:
        raise credentials_exception

    return user


def require_admin(current_user: models.User = Depends(get_current_user)):
    """
    Dependency that requires the current user to be an admin.
    Use this on routes that only admins can access.

    Usage: current_user = Depends(require_admin)
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


def log_activity(db: Session, user_id: int, action: str, detail: str = None):
    """
    Creates an activity log entry.
    Call this inside any route after a successful action.

    Example:
        log_activity(db, current_user.id, "Created Product", product.name)
    """
    log = models.ActivityLog(
        user_id=user_id,
        action=action,
        detail=detail
    )
    db.add(log)
    db.commit()