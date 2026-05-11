# backend/models.py

from sqlalchemy import Column, Integer, String, Float, Text, DateTime, Enum, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class User(Base):
    __tablename__ = "users"

    id            = Column(Integer, primary_key=True, index=True)
    username      = Column(String(50), nullable=False, unique=True, index=True)
    password      = Column(String(255), nullable=False)
    role          = Column(Enum("admin", "viewer"), nullable=False, default="viewer")
    is_active     = Column(Boolean, default=True)
    created_at    = Column(DateTime, default=datetime.utcnow)

    activity_logs = relationship("ActivityLog", back_populates="user")


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id        = Column(Integer, primary_key=True, index=True)
    action    = Column(String(255), nullable=False)
    detail    = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    user_id   = Column(Integer, ForeignKey("users.id"), nullable=True)
    user      = relationship("User", back_populates="activity_logs")


class Category(Base):
    __tablename__ = "categories"

    id          = Column(Integer, primary_key=True, index=True)
    name        = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    created_at  = Column(DateTime, default=datetime.utcnow)

    products    = relationship("Product", back_populates="category")


class Supplier(Base):
    __tablename__ = "suppliers"

    id         = Column(Integer, primary_key=True, index=True)
    name       = Column(String(100), nullable=False, index=True)
    email      = Column(String(100), nullable=True)
    phone      = Column(String(20), nullable=True)
    address    = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    products   = relationship("Product", back_populates="supplier")


class Product(Base):
    __tablename__ = "products"

    id                  = Column(Integer, primary_key=True, index=True)
    name                = Column(String(150), nullable=False, index=True)
    description         = Column(Text, nullable=True)
    price               = Column(Float, nullable=False, default=0.0)
    cost_price          = Column(Float, nullable=True, default=0.0)
    quantity            = Column(Integer, nullable=False, default=0)
    low_stock_threshold = Column(Integer, nullable=False, default=10)
    sku                 = Column(String(100), nullable=True, unique=True)
    created_at          = Column(DateTime, default=datetime.utcnow)

    category_id  = Column(Integer, ForeignKey("categories.id"), nullable=True)
    supplier_id  = Column(Integer, ForeignKey("suppliers.id"), nullable=True)

    category     = relationship("Category", back_populates="products")
    supplier     = relationship("Supplier", back_populates="products")
    transactions = relationship("Transaction", back_populates="product")

    # One product → many attachments
    attachments  = relationship("Attachment", back_populates="product",
                                foreign_keys="Attachment.product_id")


class Transaction(Base):
    __tablename__ = "transactions"

    id               = Column(Integer, primary_key=True, index=True)
    transaction_type = Column(Enum("IN", "OUT"), nullable=False)
    quantity         = Column(Integer, nullable=False)
    note             = Column(Text, nullable=True)
    created_at       = Column(DateTime, default=datetime.utcnow)

    product_id   = Column(Integer, ForeignKey("products.id"), nullable=False)
    product      = relationship("Product", back_populates="transactions")

    # One transaction → many attachments
    attachments  = relationship("Attachment", back_populates="transaction",
                                foreign_keys="Attachment.transaction_id")


# ─────────────────────────────────────────
# TABLE: Attachments
# Stores uploaded files on disk
# Links to either a product OR transaction
# ─────────────────────────────────────────
class Attachment(Base):
    __tablename__ = "attachments"

    id            = Column(Integer, primary_key=True, index=True)

    # The name we saved on disk (UUID-based to avoid conflicts)
    filename      = Column(String(255), nullable=False)

    # Full path on server disk
    filepath      = Column(String(512), nullable=False)

    # What the user originally named the file
    original_name = Column(String(255), nullable=False)

    # File type — image, pdf, doc, etc.
    file_type     = Column(String(50), nullable=True)

    # File size in bytes
    file_size     = Column(Integer, nullable=True)

    uploaded_at   = Column(DateTime, default=datetime.utcnow)

    # nullable=True — attachment belongs to EITHER product OR transaction
    product_id     = Column(Integer, ForeignKey("products.id"),     nullable=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=True)

    product     = relationship("Product",     back_populates="attachments",
                               foreign_keys=[product_id])
    transaction = relationship("Transaction", back_populates="attachments",
                               foreign_keys=[transaction_id])