# backend/routes/categories.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

import models, schemas
from database import get_db
from auth_utils import get_current_user, require_admin, log_activity

router = APIRouter(prefix="/categories", tags=["Categories"])


# GET ALL — any logged in user can view
@router.get("/", response_model=List[schemas.Category])
def get_categories(
    db:           Session     = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return db.query(models.Category).all()


# GET ONE — any logged in user
@router.get("/{category_id}", response_model=schemas.Category)
def get_category(
    category_id:  int,
    db:           Session     = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    category = db.query(models.Category).filter(
        models.Category.id == category_id
    ).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category


# CREATE — admin only
@router.post("/", response_model=schemas.Category)
def create_category(
    category:     schemas.CategoryCreate,
    db:           Session     = Depends(get_db),
    current_user: models.User = Depends(require_admin)
):
    existing = db.query(models.Category).filter(
        models.Category.name == category.name
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Category already exists")

    new_cat = models.Category(**category.dict())
    db.add(new_cat)
    db.commit()
    db.refresh(new_cat)

    log_activity(db, current_user.id, "Created Category", new_cat.name)
    return new_cat


# UPDATE — admin only
@router.put("/{category_id}", response_model=schemas.Category)
def update_category(
    category_id:  int,
    category:     schemas.CategoryCreate,
    db:           Session     = Depends(get_db),
    current_user: models.User = Depends(require_admin)
):
    existing = db.query(models.Category).filter(
        models.Category.id == category_id
    ).first()
    if not existing:
        raise HTTPException(status_code=404, detail="Category not found")

    for key, value in category.dict().items():
        setattr(existing, key, value)

    db.commit()
    db.refresh(existing)

    log_activity(db, current_user.id, "Updated Category", existing.name)
    return existing


# DELETE — admin only
@router.delete("/{category_id}")
def delete_category(
    category_id:  int,
    db:           Session     = Depends(get_db),
    current_user: models.User = Depends(require_admin)
):
    category = db.query(models.Category).filter(
        models.Category.id == category_id
    ).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    name = category.name
    db.delete(category)
    db.commit()

    log_activity(db, current_user.id, "Deleted Category", name)
    return {"message": f"Category '{name}' deleted"}