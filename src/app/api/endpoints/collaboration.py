# src/app/api/endpoints/collaboration.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.api.dependencies import get_db
from app.db import models, schemas

router = APIRouter()

@router.get("/invoices/{invoice_db_id}/comments", response_model=List[schemas.Comment])
def get_invoice_comments(invoice_db_id: int, db: Session = Depends(get_db)):
    """Retrieves all comments for a specific invoice."""
    return db.query(models.Comment).filter(models.Comment.invoice_id == invoice_db_id).order_by(models.Comment.created_at.asc()).all()

@router.post("/invoices/{invoice_db_id}/comments", response_model=schemas.Comment)
def add_invoice_comment(
    invoice_db_id: int,
    comment: schemas.CommentCreate,
    db: Session = Depends(get_db)
):
    """Adds a new comment to an invoice."""
    invoice = db.query(models.Invoice).filter(models.Invoice.id == invoice_db_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    db_comment = models.Comment(**comment.model_dump(), invoice_id=invoice_db_id)
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    return db_comment

@router.get("/invoices/{invoice_db_id}/audit-log", response_model=List[schemas.AuditLog])
def get_invoice_audit_log(invoice_db_id: int, db: Session = Depends(get_db)):
    """Retrieves the audit log for a specific invoice."""
    # Note: entity_id in AuditLog is a string, so we cast the int ID
    invoice = db.query(models.Invoice).filter(models.Invoice.id == invoice_db_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
        
    return db.query(models.AuditLog).filter(
        models.AuditLog.entity_type == 'Invoice',
        models.AuditLog.entity_id == invoice.invoice_id
    ).order_by(models.AuditLog.timestamp.desc()).all() 