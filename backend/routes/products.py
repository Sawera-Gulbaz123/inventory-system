# routes/products.py

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import models
import schemas
from database import get_db

router = APIRouter(
    prefix="/products",
    tags=["Products"]
)


# ─────────────────────────────────────────
# GET ALL PRODUCTS (with search & filter)
# Route: GET /products
# Route: GET /products?search=iphone
# Route: GET /products?category_id=1
# Route: GET /products?low_stock=true
# ─────────────────────────────────────────
@router.get("/", response_model=List[schemas.Product])
def get_products(
    # Query() defines URL parameters (the ?search=... part)
    # None means it's optional
    search: Optional[str] = Query(None, description="Search by product name"),
    category_id: Optional[int] = Query(None, description="Filter by category"),
    low_stock: Optional[bool] = Query(None, description="Show only low stock items"),
    db: Session = Depends(get_db)
):
    # Start with a base query - we'll add filters to it
    query = db.query(models.Product)

    # If search term provided, filter by name
    # ilike is case-insensitive LIKE
    # %search% means "contains search anywhere in the name"
    if search:
        query = query.filter(models.Product.name.ilike(f"%{search}%"))

    # If category filter provided
    if category_id:
        query = query.filter(models.Product.category_id == category_id)

    # If low_stock filter provided
    # Show products where quantity <= low_stock_threshold
    if low_stock:
        query = query.filter(
            models.Product.quantity <= models.Product.low_stock_threshold
        )

    return query.all()


# GET SINGLE PRODUCT
@router.get("/{product_id}", response_model=schemas.Product)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(
        models.Product.id == product_id
    ).first()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    return product


# ─────────────────────────────────────────
# CREATE PRODUCT
# Route: POST /products
# ─────────────────────────────────────────
@router.post("/", response_model=schemas.Product)
def create_product(product: schemas.ProductCreate, db: Session = Depends(get_db)):
    # Check SKU uniqueness if provided
    if product.sku:
        existing = db.query(models.Product).filter(
            models.Product.sku == product.sku
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="SKU already exists")

    new_product = models.Product(**product.dict())
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return new_product


# ─────────────────────────────────────────
# UPDATE PRODUCT
# Route: PUT /products/1
# ─────────────────────────────────────────
@router.put("/{product_id}", response_model=schemas.Product)
def update_product(product_id: int, product: schemas.ProductUpdate, db: Session = Depends(get_db)):
    existing = db.query(models.Product).filter(
        models.Product.id == product_id
    ).first()

    if not existing:
        raise HTTPException(status_code=404, detail="Product not found")

    # exclude_unset=True means only update fields that were actually sent
    # If user only sends price, only price gets updated
    # Without this, missing fields would be set to None
    update_data = product.dict(exclude_unset=True)

    for key, value in update_data.items():
        setattr(existing, key, value)

    db.commit()
    db.refresh(existing)
    return existing


# ─────────────────────────────────────────
# DELETE PRODUCT
# Route: DELETE /products/1
# ─────────────────────────────────────────
@router.delete("/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(
        models.Product.id == product_id
    ).first()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    db.delete(product)
    db.commit()
    return {"message": f"Product {product_id} deleted successfully"}