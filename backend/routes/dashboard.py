# backend/routes/dashboard.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
import models, schemas
from database import get_db
from auth_utils import get_current_user

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats", response_model=schemas.DashboardStats)
def get_dashboard_stats(
    db:           Session     = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    total_products   = db.query(func.count(models.Product.id)).scalar()
    total_categories = db.query(func.count(models.Category.id)).scalar()
    total_suppliers  = db.query(func.count(models.Supplier.id)).scalar()

    low_stock_count  = db.query(func.count(models.Product.id)).filter(
        models.Product.quantity <= models.Product.low_stock_threshold
    ).scalar()

    # Total value at selling price — what the stock is worth if sold
    total_stock_value = db.query(
        func.coalesce(func.sum(models.Product.price * models.Product.quantity), 0)
    ).scalar()

    # Total value at cost price — what you paid for the stock
    # coalesce handles NULL cost_price by treating it as 0
    total_cost_value = db.query(
        func.coalesce(
            func.sum(
                func.coalesce(models.Product.cost_price, 0) * models.Product.quantity
            ), 0
        )
    ).scalar()

    # Profit = what you'd earn if you sold everything at selling price
    # minus what you paid for it
    total_profit_value = float(total_stock_value) - float(total_cost_value)

    recent_transactions = db.query(models.Transaction).order_by(
        models.Transaction.created_at.desc()
    ).limit(5).all()

    return {
        "total_products":      total_products,
        "total_categories":    total_categories,
        "total_suppliers":     total_suppliers,
        "low_stock_count":     low_stock_count,
        "total_stock_value":   float(total_stock_value),
        "total_cost_value":    float(total_cost_value),
        "total_profit_value":  total_profit_value,
        "recent_transactions": recent_transactions,
    }