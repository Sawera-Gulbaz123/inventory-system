# backend/routes/attachments.py

import os
import uuid
import shutil
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional

import models
import schemas
from database import get_db
from auth_utils import get_current_user, log_activity

router = APIRouter(prefix="/attachments", tags=["Attachments"])

# ── Upload directory ─────────────────────────────────────────────
# Stored inside backend/uploads/
# Created automatically if it does not exist
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Allowed file types for security
ALLOWED_EXTENSIONS = {
    '.jpg', '.jpeg', '.png', '.gif', '.webp',  # images
    '.pdf',                                     # documents
    '.doc', '.docx',                            # word
    '.xls', '.xlsx',                            # excel
    '.txt', '.csv',                             # text
    '.zip', '.rar',                             # archives
}

# Max file size: 10MB
MAX_FILE_SIZE = 10 * 1024 * 1024


# ── UPLOAD FILE ──────────────────────────────────────────────────
@router.post("/upload", response_model=schemas.Attachment)
async def upload_file(
    file:           UploadFile        = File(...),
    product_id:     Optional[int]     = Form(None),
    transaction_id: Optional[int]     = Form(None),
    db:             Session           = Depends(get_db),
    current_user:   models.User       = Depends(get_current_user),
):
    # Must be linked to either a product or transaction
    if not product_id and not transaction_id:
        raise HTTPException(
            status_code=400,
            detail="Must provide either product_id or transaction_id"
        )

    # Check file extension
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type '{ext}' not allowed"
        )

    # Read file content to check size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail="File too large. Maximum size is 10MB"
        )

    # Generate unique filename to prevent conflicts
    # e.g. "invoice.pdf" → "a3f9b1c2-uuid-here.pdf"
    unique_name = f"{uuid.uuid4()}{ext}"
    file_path   = os.path.join(UPLOAD_DIR, unique_name)

    # Write file to disk
    with open(file_path, "wb") as f:
        f.write(content)

    # Determine file type category for display
    image_exts = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
    file_type  = "image" if ext in image_exts else ext.lstrip('.')

    # Save record to database
    attachment = models.Attachment(
        filename       = unique_name,
        filepath       = file_path,
        original_name  = file.filename,
        file_type      = file_type,
        file_size      = len(content),
        product_id     = product_id,
        transaction_id = transaction_id,
    )

    db.add(attachment)
    db.commit()
    db.refresh(attachment)

    # Log the action
    target = f"product #{product_id}" if product_id else f"transaction #{transaction_id}"
    log_activity(db, current_user.id, "Uploaded File", f"{file.filename} → {target}")

    return attachment


# ── GET ATTACHMENTS FOR A PRODUCT ────────────────────────────────
@router.get("/product/{product_id}", response_model=List[schemas.Attachment])
def get_product_attachments(
    product_id:   int,
    db:           Session     = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return db.query(models.Attachment).filter(
        models.Attachment.product_id == product_id
    ).order_by(models.Attachment.uploaded_at.desc()).all()


# ── GET ATTACHMENTS FOR A TRANSACTION ────────────────────────────
@router.get("/transaction/{transaction_id}", response_model=List[schemas.Attachment])
def get_transaction_attachments(
    transaction_id: int,
    db:             Session     = Depends(get_db),
    current_user:   models.User = Depends(get_current_user),
):
    return db.query(models.Attachment).filter(
        models.Attachment.transaction_id == transaction_id
    ).order_by(models.Attachment.uploaded_at.desc()).all()


# ── GET ALL ATTACHMENTS (for gallery) ────────────────────────────
@router.get("/", response_model=List[schemas.Attachment])
def get_all_attachments(
    db:           Session     = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return db.query(models.Attachment).order_by(
        models.Attachment.uploaded_at.desc()
    ).all()


# ── DOWNLOAD / VIEW FILE ─────────────────────────────────────────
@router.get("/download/{attachment_id}")
def download_file(
    attachment_id: int,
    db:            Session     = Depends(get_db),
    current_user:  models.User = Depends(get_current_user),
):
    attachment = db.query(models.Attachment).filter(
        models.Attachment.id == attachment_id
    ).first()

    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")

    if not os.path.exists(attachment.filepath):
        raise HTTPException(status_code=404, detail="File not found on disk")

    return FileResponse(
        path       = attachment.filepath,
        filename   = attachment.original_name,
        media_type = "application/octet-stream"
    )


# ── VIEW IMAGE (inline, not download) ────────────────────────────
@router.get("/view/{attachment_id}")
def view_file(
    attachment_id: int,
    db:            Session     = Depends(get_db),
    current_user:  models.User = Depends(get_current_user),
):
    attachment = db.query(models.Attachment).filter(
        models.Attachment.id == attachment_id
    ).first()

    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")

    if not os.path.exists(attachment.filepath):
        raise HTTPException(status_code=404, detail="File not found on disk")

    # Detect correct media type for inline viewing
    ext        = os.path.splitext(attachment.filename)[1].lower()
    media_type = {
        '.jpg':  'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png':  'image/png',
        '.gif':  'image/gif',
        '.webp': 'image/webp',
        '.pdf':  'application/pdf',
    }.get(ext, 'application/octet-stream')

    return FileResponse(
        path       = attachment.filepath,
        media_type = media_type,
    )


# ── DELETE ATTACHMENT ─────────────────────────────────────────────
@router.delete("/{attachment_id}")
def delete_attachment(
    attachment_id: int,
    db:            Session     = Depends(get_db),
    current_user:  models.User = Depends(get_current_user),
):
    attachment = db.query(models.Attachment).filter(
        models.Attachment.id == attachment_id
    ).first()

    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")

    # Delete file from disk first
    if os.path.exists(attachment.filepath):
        os.remove(attachment.filepath)

    name = attachment.original_name
    db.delete(attachment)
    db.commit()

    log_activity(db, current_user.id, "Deleted File", name)
    return {"message": f"Attachment '{name}' deleted"}