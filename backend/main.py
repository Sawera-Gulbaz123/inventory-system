# backend/main.py

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from database import Base, engine
import models

from routes import categories, suppliers, products, transactions, dashboard
from routes import auth, users, attachments, backup

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Inventory Management System",
    description="Complete inventory system",
    version="4.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router,         prefix="/api")
app.include_router(users.router,        prefix="/api")
app.include_router(categories.router,   prefix="/api")
app.include_router(suppliers.router,    prefix="/api")
app.include_router(products.router,     prefix="/api")
app.include_router(transactions.router, prefix="/api")
app.include_router(dashboard.router,    prefix="/api")
app.include_router(attachments.router,  prefix="/api")
app.include_router(backup.router,       prefix="/api")

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

BUILD_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend", "build")

if os.path.exists(BUILD_DIR):
    app.mount(
        "/static",
        StaticFiles(directory=os.path.join(BUILD_DIR, "static")),
        name="static"
    )

    @app.get("/")
    def serve_root():
        return FileResponse(os.path.join(BUILD_DIR, "index.html"))

    @app.get("/{full_path:path}")
    def serve_frontend(full_path: str):
        if full_path.startswith("api") or full_path.startswith("uploads"):
            return {"detail": "Not found"}
        file_path = os.path.join(BUILD_DIR, full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(BUILD_DIR, "index.html"))
else:
    @app.get("/")
    def root():
        return {"message": "Inventory Management System API ✅"}