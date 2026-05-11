# backend/routes/products.py

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

import models, schemas
from database import get_db
from auth_utils import get_current_user, require_admin, log_activity

router = APIRouter(prefix="/products", tags=["Products"])


@router.get("/", response_model=List[schemas.Product])
def get_products(
    search:       Optional[str]  = Query(None),
    category_id:  Optional[int]  = Query(None),
    low_stock:    Optional[bool] = Query(None),
    db:           Session        = Depends(get_db),
    current_user: models.User    = Depends(get_current_user)
):
    query = db.query(models.Product)
    if search:
        query = query.filter(models.Product.name.ilike(f"%{search}%"))
    if category_id:
        query = query.filter(models.Product.category_id == category_id)
    if low_stock:
        query = query.filter(
            models.Product.quantity <= models.Product.low_stock_threshold
        )
    return query.all()


@router.get("/{product_id}", response_model=schemas.Product)
def get_product(
    product_id:   int,
    db:           Session     = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    product = db.query(models.Product).filter(
        models.Product.id == product_id
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.post("/", response_model=schemas.Product)
def create_product(
    product:      schemas.ProductCreate,
    db:           Session     = Depends(get_db),
    current_user: models.User = Depends(require_admin)
):
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

    log_activity(db, current_user.id, "Created Product", new_product.name)
    return new_product


@router.put("/{product_id}", response_model=schemas.Product)
def update_product(
    product_id:   int,
    product:      schemas.ProductUpdate,
    db:           Session     = Depends(get_db),
    current_user: models.User = Depends(require_admin)
):
    existing = db.query(models.Product).filter(
        models.Product.id == product_id
    ).first()
    if not existing:
        raise HTTPException(status_code=404, detail="Product not found")

    for key, value in product.dict(exclude_unset=True).items():
        setattr(existing, key, value)

    db.commit()
    db.refresh(existing)

    log_activity(db, current_user.id, "Updated Product", existing.name)
    return existing


@router.delete("/{product_id}")
def delete_product(
    product_id:   int,
    db:           Session     = Depends(get_db),
    current_user: models.User = Depends(require_admin)
):
    product = db.query(models.Product).filter(
        models.Product.id == product_id
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    name = product.name
    db.delete(product)
    db.commit()

    log_activity(db, current_user.id, "Deleted Product", name)
    return {"message": f"Product '{name}' deleted"}