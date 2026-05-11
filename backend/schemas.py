# backend/schemas.py

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ═══════════════════════════════════════
# AUTH SCHEMAS
# ═══════════════════════════════════════

class Token(BaseModel):
    access_token: str
    token_type:   str
    role:         str
    username:     str

class TokenData(BaseModel):
    username: Optional[str] = None


# ═══════════════════════════════════════
# USER SCHEMAS
# ═══════════════════════════════════════

class UserCreate(BaseModel):
    username: str = Field(..., example="john")
    password: str = Field(..., min_length=4)
    role:     str = Field("viewer")

class UserUpdate(BaseModel):
    username:  Optional[str]  = None
    password:  Optional[str]  = Field(None, min_length=4)
    role:      Optional[str]  = None
    is_active: Optional[bool] = None

class UserResponse(BaseModel):
    id:         int
    username:   str
    role:       str
    is_active:  bool
    created_at: datetime

    class Config:
        from_attributes = True


# ═══════════════════════════════════════
# ACTIVITY LOG SCHEMA
# ═══════════════════════════════════════

class ActivityLogResponse(BaseModel):
    id:        int
    action:    str
    detail:    Optional[str] = None
    timestamp: datetime
    user_id:   Optional[int] = None
    user:      Optional[UserResponse] = None

    class Config:
        from_attributes = True


# ═══════════════════════════════════════
# ATTACHMENT SCHEMA
# Defined early — referenced by Product
# and Transaction response schemas
# ═══════════════════════════════════════

class Attachment(BaseModel):
    id:            int
    filename:      str
    original_name: str
    file_type:     Optional[str] = None
    file_size:     Optional[int] = None
    uploaded_at:   datetime
    product_id:    Optional[int] = None
    transaction_id:Optional[int] = None

    class Config:
        from_attributes = True


# ═══════════════════════════════════════
# CATEGORY SCHEMAS
# ═══════════════════════════════════════

class CategoryBase(BaseModel):
    name:        str            = Field(..., example="Electronics")
    description: Optional[str] = None

class CategoryCreate(CategoryBase):
    pass

class Category(CategoryBase):
    id:         int
    created_at: datetime

    class Config:
        from_attributes = True


# ═══════════════════════════════════════
# SUPPLIER SCHEMAS
# ═══════════════════════════════════════

class SupplierBase(BaseModel):
    name:    str            = Field(..., example="Tech Distributors")
    email:   Optional[str] = None
    phone:   Optional[str] = None
    address: Optional[str] = None

class SupplierCreate(SupplierBase):
    pass

class Supplier(SupplierBase):
    id:         int
    created_at: datetime

    class Config:
        from_attributes = True


# ═══════════════════════════════════════
# PRODUCT SCHEMAS
# ═══════════════════════════════════════

class ProductBase(BaseModel):
    name:                str            = Field(..., example="iPhone 15")
    description:         Optional[str] = None
    price:               float          = Field(..., gt=0)
    cost_price:          Optional[float] = Field(0.0, ge=0)
    quantity:            int            = Field(0, ge=0)
    low_stock_threshold: int            = Field(10, ge=0)
    sku:                 Optional[str] = None
    category_id:         Optional[int] = None
    supplier_id:         Optional[int] = None

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name:                Optional[str]   = None
    description:         Optional[str]   = None
    price:               Optional[float] = Field(None, gt=0)
    cost_price:          Optional[float] = Field(None, ge=0)
    quantity:            Optional[int]   = Field(None, ge=0)
    low_stock_threshold: Optional[int]   = Field(None, ge=0)
    sku:                 Optional[str]   = None
    category_id:         Optional[int]   = None
    supplier_id:         Optional[int]   = None

class Product(ProductBase):
    id:          int
    created_at:  datetime
    category:    Optional[Category]    = None
    supplier:    Optional[Supplier]    = None
    attachments: List[Attachment]      = []

    class Config:
        from_attributes = True


# ═══════════════════════════════════════
# TRANSACTION SCHEMAS
# ═══════════════════════════════════════

class TransactionBase(BaseModel):
    transaction_type: str = Field(..., example="IN")
    quantity:         int = Field(..., gt=0)
    note:             Optional[str] = None
    product_id:       int

class TransactionCreate(TransactionBase):
    pass

class Transaction(TransactionBase):
    id:          int
    created_at:  datetime
    product:     Optional[Product]  = None
    attachments: List[Attachment]   = []

    class Config:
        from_attributes = True


# ═══════════════════════════════════════
# DASHBOARD SCHEMA
# ═══════════════════════════════════════

class DashboardStats(BaseModel):
    total_products:      int
    total_categories:    int
    total_suppliers:     int
    low_stock_count:     int
    total_stock_value:   float
    total_cost_value:    float
    total_profit_value:  float
    recent_transactions: List[Transaction] = []

    class Config:
        from_attributes = True