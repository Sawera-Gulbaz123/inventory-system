# routes/suppliers.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import models
import schemas
from database import get_db

router = APIRouter(
    prefix="/suppliers",
    tags=["Suppliers"]
)


# GET ALL SUPPLIERS
@router.get("/", response_model=List[schemas.Supplier])
def get_suppliers(db: Session = Depends(get_db)):
    return db.query(models.Supplier).all()


# GET SINGLE SUPPLIER
@router.get("/{supplier_id}", response_model=schemas.Supplier)
def get_supplier(supplier_id: int, db: Session = Depends(get_db)):
    supplier = db.query(models.Supplier).filter(
        models.Supplier.id == supplier_id
    ).first()

    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    return supplier


# CREATE SUPPLIER
@router.post("/", response_model=schemas.Supplier)
def create_supplier(supplier: schemas.SupplierCreate, db: Session = Depends(get_db)):
    new_supplier = models.Supplier(**supplier.dict())
    db.add(new_supplier)
    db.commit()
    db.refresh(new_supplier)
    return new_supplier


# UPDATE SUPPLIER
@router.put("/{supplier_id}", response_model=schemas.Supplier)
def update_supplier(supplier_id: int, supplier: schemas.SupplierCreate, db: Session = Depends(get_db)):
    existing = db.query(models.Supplier).filter(
        models.Supplier.id == supplier_id
    ).first()

    if not existing:
        raise HTTPException(status_code=404, detail="Supplier not found")

    for key, value in supplier.dict().items():
        setattr(existing, key, value)

    db.commit()
    db.refresh(existing)
    return existing


# DELETE SUPPLIER
@router.delete("/{supplier_id}")
def delete_supplier(supplier_id: int, db: Session = Depends(get_db)):
    supplier = db.query(models.Supplier).filter(
        models.Supplier.id == supplier_id
    ).first()

    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    db.delete(supplier)
    db.commit()
    return {"message": f"Supplier {supplier_id} deleted successfully"}