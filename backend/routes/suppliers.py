# backend/routes/suppliers.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

import models, schemas
from database import get_db
from auth_utils import get_current_user, require_admin, log_activity

router = APIRouter(prefix="/suppliers", tags=["Suppliers"])


@router.get("/", response_model=List[schemas.Supplier])
def get_suppliers(
    db:           Session     = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return db.query(models.Supplier).all()


@router.get("/{supplier_id}", response_model=schemas.Supplier)
def get_supplier(
    supplier_id:  int,
    db:           Session     = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    supplier = db.query(models.Supplier).filter(
        models.Supplier.id == supplier_id
    ).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return supplier


@router.post("/", response_model=schemas.Supplier)
def create_supplier(
    supplier:     schemas.SupplierCreate,
    db:           Session     = Depends(get_db),
    current_user: models.User = Depends(require_admin)
):
    new_sup = models.Supplier(**supplier.dict())
    db.add(new_sup)
    db.commit()
    db.refresh(new_sup)

    log_activity(db, current_user.id, "Created Supplier", new_sup.name)
    return new_sup


@router.put("/{supplier_id}", response_model=schemas.Supplier)
def update_supplier(
    supplier_id:  int,
    supplier:     schemas.SupplierCreate,
    db:           Session     = Depends(get_db),
    current_user: models.User = Depends(require_admin)
):
    existing = db.query(models.Supplier).filter(
        models.Supplier.id == supplier_id
    ).first()
    if not existing:
        raise HTTPException(status_code=404, detail="Supplier not found")

    for key, value in supplier.dict().items():
        setattr(existing, key, value)

    db.commit()
    db.refresh(existing)

    log_activity(db, current_user.id, "Updated Supplier", existing.name)
    return existing


@router.delete("/{supplier_id}")
def delete_supplier(
    supplier_id:  int,
    db:           Session     = Depends(get_db),
    current_user: models.User = Depends(require_admin)
):
    supplier = db.query(models.Supplier).filter(
        models.Supplier.id == supplier_id
    ).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    name = supplier.name
    db.delete(supplier)
    db.commit()

    log_activity(db, current_user.id, "Deleted Supplier", name)
    return {"message": f"Supplier '{name}' deleted"}