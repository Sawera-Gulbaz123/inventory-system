# models.py

# Column defines a column in the table
# Integer, String etc. are the data types for columns
# ForeignKey links two tables together
# Text is for long text (like descriptions)
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, Enum
from sqlalchemy import ForeignKey

# relationship lets us access related data easily
# e.g. product.category gives us the full category object
from sqlalchemy.orm import relationship

# datetime for timestamps
from datetime import datetime

# We import Base from our database.py
# Every model MUST inherit from Base
from database import Base


# ─────────────────────────────────────────
# TABLE 1: Categories
# ─────────────────────────────────────────
class Category(Base):
    # __tablename__ tells SQLAlchemy what to name the table in MySQL
    __tablename__ = "categories"

    # Primary key - unique ID for each category, auto increments (1, 2, 3...)
    id = Column(Integer, primary_key=True, index=True)

    # name must exist (nullable=False) and must be unique
    # index=True makes searching by name faster
    name = Column(String(100), nullable=False, unique=True, index=True)

    # Description is optional (nullable=True is default)
    description = Column(Text, nullable=True)

    # Automatically set to current time when a category is created
    created_at = Column(DateTime, default=datetime.utcnow)

    # This is not a column - it's a relationship
    # It lets us do category.products to get all products in this category
    # back_populates="category" means Product also knows about this link
    products = relationship("Product", back_populates="category")


# ─────────────────────────────────────────
# TABLE 2: Suppliers
# ─────────────────────────────────────────
class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(100), nullable=False, index=True)

    # Contact details - all optional
    email = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)
    address = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    # One supplier can supply many products
    products = relationship("Product", back_populates="supplier")


# ─────────────────────────────────────────
# TABLE 3: Products
# ─────────────────────────────────────────
class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(150), nullable=False, index=True)

    description = Column(Text, nullable=True)

    # Price uses Float for decimal values like 9.99
    price = Column(Float, nullable=False, default=0.0)

    # Current stock quantity
    quantity = Column(Integer, nullable=False, default=0)

    # When quantity drops below this number, we show a low stock alert
    # Default is 10 - meaning alert when less than 10 items remain
    low_stock_threshold = Column(Integer, nullable=False, default=10)

    # SKU = Stock Keeping Unit - a unique code for each product
    # Like a barcode identifier. e.g. "ELEC-001"
    sku = Column(String(100), nullable=True, unique=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    # ForeignKey links this column to the id column of categories table
    # This means every product MUST belong to a category
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)

    # Links to suppliers table
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True)

    # These let us do product.category and product.supplier
    # back_populates connects back to the relationship in Category/Supplier
    category = relationship("Category", back_populates="products")
    supplier = relationship("Supplier", back_populates="products")

    # One product can have many transactions
    transactions = relationship("Transaction", back_populates="product")


# ─────────────────────────────────────────
# TABLE 4: Transactions
# ─────────────────────────────────────────
class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)

    # Enum means this column can ONLY be one of these two values
    # IN  = stock coming in (new purchase/restock)
    # OUT = stock going out (sale/usage)
    transaction_type = Column(Enum("IN", "OUT"), nullable=False)

    # How many units were added or removed
    quantity = Column(Integer, nullable=False)

    # Optional note about this transaction
    # e.g. "Restocked from supplier" or "Sold to customer"
    note = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Every transaction must be linked to a product
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)

    # This lets us do transaction.product to get full product details
    product = relationship("Product", back_populates="transactions")