# main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import Base, engine
import models

# Import all routers
from routes import categories, suppliers, products, transactions, dashboard

# Create all tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Inventory Management System",
    description="A complete inventory system API",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register all routers
# include_router attaches each router's routes to the main app
app.include_router(categories.router)
app.include_router(suppliers.router)
app.include_router(products.router)
app.include_router(transactions.router)
app.include_router(dashboard.router)

@app.get("/")
def root():
    return {"message": "Inventory Management System API is running ✅"}