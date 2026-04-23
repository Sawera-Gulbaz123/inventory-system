# routes/dashboard.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
import models
import schemas
from database import get_db

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"]
)


@router.get("/stats", response_model=schemas.DashboardStats)
def get_dashboard_stats(db: Session = Depends(get_db)):

    # Count total products
    # func.count() is SQLAlchemy's way of doing COUNT() in SQL
    total_products = db.query(func.count(models.Product.id)).scalar()

    # Count total categories
    total_categories = db.query(func.count(models.Category.id)).scalar()

    # Count total suppliers
    total_suppliers = db.query(func.count(models.Supplier.id)).scalar()

    # Count products where quantity <= low_stock_threshold
    low_stock_count = db.query(func.count(models.Product.id)).filter(
        models.Product.quantity <= models.Product.low_stock_threshold
    ).scalar()

    # Calculate total stock value
    # func.sum(price * quantity) for all products
    # coalesce means "if null, return 0" — handles empty database
    total_stock_value = db.query(
        func.coalesce(func.sum(models.Product.price * models.Product.quantity), 0)
    ).scalar()

    # Get 5 most recent transactions
    recent_transactions = db.query(models.Transaction).order_by(
        models.Transaction.created_at.desc()
    ).limit(5).all()

    return {
        "total_products": total_products,
        "total_categories": total_categories,
        "total_suppliers": total_suppliers,
        "low_stock_count": low_stock_count,
        "total_stock_value": float(total_stock_value),
        "recent_transactions": recent_transactions
    }