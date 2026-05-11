# backend/routes/transactions.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

import models, schemas
from database import get_db
from auth_utils import get_current_user, require_admin, log_activity

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.get("/", response_model=List[schemas.Transaction])
def get_transactions(
    db:           Session     = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return db.query(models.Transaction).order_by(
        models.Transaction.created_at.desc()
    ).all()


@router.get("/product/{product_id}", response_model=List[schemas.Transaction])
def get_product_transactions(
    product_id:   int,
    db:           Session     = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    return db.query(models.Transaction).filter(
        models.Transaction.product_id == product_id
    ).order_by(models.Transaction.created_at.desc()).all()


@router.post("/", response_model=schemas.Transaction)
def create_transaction(
    transaction:  schemas.TransactionCreate,
    db:           Session     = Depends(get_db),
    current_user: models.User = Depends(require_admin)
):
    product = db.query(models.Product).filter(
        models.Product.id == transaction.product_id
    ).first()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if transaction.transaction_type not in ["IN", "OUT"]:
        raise HTTPException(status_code=400, detail="Type must be IN or OUT")

    if transaction.transaction_type == "OUT":
        if product.quantity < transaction.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient stock. Available: {product.quantity}"
            )
        product.quantity -= transaction.quantity
    else:
        product.quantity += transaction.quantity

    new_transaction = models.Transaction(**transaction.dict())
    db.add(new_transaction)
    db.commit()
    db.refresh(new_transaction)

    log_activity(
        db, current_user.id,
        f"Stock {transaction.transaction_type}",
        f"{transaction.quantity} units of '{product.name}'"
    )
    return new_transaction


@router.delete("/{transaction_id}")
def delete_transaction(
    transaction_id: int,
    db:             Session     = Depends(get_db),
    current_user:   models.User = Depends(require_admin)
):
    t = db.query(models.Transaction).filter(
        models.Transaction.id == transaction_id
    ).first()
    if not t:
        raise HTTPException(status_code=404, detail="Transaction not found")

    db.delete(t)
    db.commit()

    log_activity(db, current_user.id, "Deleted Transaction", f"ID {transaction_id}")
    return {"message": f"Transaction {transaction_id} deleted"}