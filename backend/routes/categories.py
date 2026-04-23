# routes/categories.py

# APIRouter is like a mini FastAPI app
# We create one router per feature and combine them in main.py
# This keeps code organized — all category routes stay here
from fastapi import APIRouter, Depends, HTTPException

# Session is the type for our database connection
from sqlalchemy.orm import Session

# List is for returning arrays of items
from typing import List

# Import our database dependency, models and schemas
import models
import schemas
from database import get_db

# Create a router with a prefix
# prefix="/categories" means all routes here start with /categories
# tags=["Categories"] groups them in the API docs
router = APIRouter(
    prefix="/categories",
    tags=["Categories"]
)


# ─────────────────────────────────────────
# GET ALL CATEGORIES
# Route: GET /categories
# ─────────────────────────────────────────
@router.get("/", response_model=List[schemas.Category])
def get_categories(db: Session = Depends(get_db)):
    # Depends(get_db) automatically:
    # 1. Opens a database session
    # 2. Passes it to this function as 'db'
    # 3. Closes it when the function finishes
    #
    # db.query(models.Category) → SELECT * FROM categories
    # .all() → fetch all rows
    categories = db.query(models.Category).all()
    return categories


# ─────────────────────────────────────────
# GET SINGLE CATEGORY
# Route: GET /categories/1
# ─────────────────────────────────────────
@router.get("/{category_id}", response_model=schemas.Category)
def get_category(category_id: int, db: Session = Depends(get_db)):
    # {category_id} in the route captures the number from the URL
    # e.g. /categories/3 → category_id = 3
    #
    # .filter() is like WHERE in SQL
    # models.Category.id == category_id → WHERE id = category_id
    # .first() → fetch only the first matching row
    category = db.query(models.Category).filter(
        models.Category.id == category_id
    ).first()

    # If nothing found, return 404 error
    # HTTPException is FastAPI's way of sending error responses
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    return category


# ─────────────────────────────────────────
# CREATE CATEGORY
# Route: POST /categories
# ─────────────────────────────────────────
@router.post("/", response_model=schemas.Category)
def create_category(category: schemas.CategoryCreate, db: Session = Depends(get_db)):
    # category: schemas.CategoryCreate means FastAPI will:
    # 1. Read the JSON body from the request
    # 2. Validate it against CategoryCreate schema
    # 3. Pass it here as 'category' object

    # Check if category with same name already exists
    existing = db.query(models.Category).filter(
        models.Category.name == category.name
    ).first()

    if existing:
        # 400 = Bad Request — user sent invalid data
        raise HTTPException(status_code=400, detail="Category already exists")

    # Create a new SQLAlchemy model instance
    # **category.dict() unpacks the schema into keyword arguments
    # same as: models.Category(name=category.name, description=category.description)
    new_category = models.Category(**category.dict())

    # db.add() → stages the new record (like git add)
    db.add(new_category)

    # db.commit() → saves to database permanently (like git commit)
    db.commit()

    # db.refresh() → reloads the object from DB to get generated fields
    # like id and created_at which MySQL generated
    db.refresh(new_category)

    return new_category


# ─────────────────────────────────────────
# UPDATE CATEGORY
# Route: PUT /categories/1
# ─────────────────────────────────────────
@router.put("/{category_id}", response_model=schemas.Category)
def update_category(category_id: int, category: schemas.CategoryCreate, db: Session = Depends(get_db)):
    # First find the existing category
    existing = db.query(models.Category).filter(
        models.Category.id == category_id
    ).first()

    if not existing:
        raise HTTPException(status_code=404, detail="Category not found")

    # Update each field
    # We loop through the updated data and set each field
    for key, value in category.dict().items():
        setattr(existing, key, value)
    # setattr(existing, "name", "Electronics") is same as existing.name = "Electronics"

    db.commit()
    db.refresh(existing)
    return existing


# ─────────────────────────────────────────
# DELETE CATEGORY
# Route: DELETE /categories/1
# ─────────────────────────────────────────
@router.delete("/{category_id}")
def delete_category(category_id: int, db: Session = Depends(get_db)):
    category = db.query(models.Category).filter(
        models.Category.id == category_id
    ).first()

    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    # db.delete() removes the record
    db.delete(category)
    db.commit()

    # We return a simple message instead of the deleted object
    return {"message": f"Category {category_id} deleted successfully"}