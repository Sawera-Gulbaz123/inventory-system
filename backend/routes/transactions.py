# routes/transactions.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import models
import schemas
from database import get_db

router = APIRouter(
    prefix="/transactions",
    tags=["Transactions"]
)


# GET ALL TRANSACTIONS
@router.get("/", response_model=List[schemas.Transaction])
def get_transactions(db: Session = Depends(get_db)):
    # order_by desc means newest transactions first
    return db.query(models.Transaction).order_by(
        models.Transaction.created_at.desc()
    ).all()


# GET TRANSACTIONS FOR A SPECIFIC PRODUCT
@router.get("/product/{product_id}", response_model=List[schemas.Transaction])
def get_product_transactions(product_id: int, db: Session = Depends(get_db)):
    return db.query(models.Transaction).filter(
        models.Transaction.product_id == product_id
    ).order_by(models.Transaction.created_at.desc()).all()


# ─────────────────────────────────────────
# CREATE TRANSACTION
# This is the most important route
# When stock comes IN or goes OUT, we:
# 1. Create the transaction record
# 2. Automatically update the product quantity
# ─────────────────────────────────────────
@router.post("/", response_model=schemas.Transaction)
def create_transaction(transaction: schemas.TransactionCreate, db: Session = Depends(get_db)):
    # First verify the product exists
    product = db.query(models.Product).filter(
        models.Product.id == transaction.product_id
    ).first()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Validate transaction type
    if transaction.transaction_type not in ["IN", "OUT"]:
        raise HTTPException(status_code=400, detail="Transaction type must be IN or OUT")

    # If stock going OUT, make sure we have enough
    if transaction.transaction_type == "OUT":
        if product.quantity < transaction.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient stock. Available: {product.quantity}, Requested: {transaction.quantity}"
            )
        # Subtract from stock
        product.quantity -= transaction.quantity

    # If stock coming IN, add to stock
    elif transaction.transaction_type == "IN":
        product.quantity += transaction.quantity

    # Create the transaction record
    new_transaction = models.Transaction(**transaction.dict())
    db.add(new_transaction)

    # This single commit saves BOTH the transaction AND the updated quantity
    # If either fails, both are rolled back — this is called atomicity
    db.commit()
    db.refresh(new_transaction)
    return new_transaction


# DELETE TRANSACTION
@router.delete("/{transaction_id}")
def delete_transaction(transaction_id: int, db: Session = Depends(get_db)):
    transaction = db.query(models.Transaction).filter(
        models.Transaction.id == transaction_id
    ).first()

    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    db.delete(transaction)
    db.commit()
    return {"message": f"Transaction {transaction_id} deleted successfully"}