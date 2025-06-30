# src/app/api/endpoints/collaboration.py
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel

from app.api.dependencies import get_db
from app.db import models, schemas
from app.utils.auditing import log_audit_event

router = APIRouter()

class CommunicationRequest(BaseModel):
    message: str

@router.post("/invoices/{invoice_db_id}/request-vendor-response", status_code=202, summary="Send message to Vendor")
def request_vendor_response(
    invoice_db_id: int, 
    request: CommunicationRequest,
    db: Session = Depends(get_db)
):
    """Logs an email communication to a vendor and updates the invoice status."""
    invoice = db.query(models.Invoice).filter(models.Invoice.id == invoice_db_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    invoice.status = models.DocumentStatus.pending_vendor_response
    
    comment = models.Comment(
        invoice_id=invoice_db_id,
        user="AP Team",
        text=f"Sent to vendor: {request.message}",
        type="vendor"
    )
    db.add(comment)

    log_audit_event(db, invoice_db_id=invoice_db_id, user="AP Team", action="Vendor Communication Sent", details={"message": request.message})
    
    db.commit()
    return {"message": "Vendor communication logged and status updated."}

@router.post("/invoices/{invoice_db_id}/request-internal-response", status_code=202, summary="Send message to Internal Team")
def request_internal_response(
    invoice_db_id: int, 
    request: CommunicationRequest,
    db: Session = Depends(get_db)
):
    """Logs an internal communication and updates the invoice status."""
    invoice = db.query(models.Invoice).filter(models.Invoice.id == invoice_db_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    invoice.status = models.DocumentStatus.pending_internal_response
    
    comment = models.Comment(
        invoice_id=invoice_db_id,
        user="AP Team",
        text=f"Sent for internal review: {request.message}",
        type="internal_review"
    )
    db.add(comment)

    log_audit_event(db, invoice_db_id=invoice_db_id, user="AP Team", action="Internal Review Requested", details={"message": request.message})
    
    db.commit()
    return {"message": "Internal review requested and status updated."}

@router.get("/invoices/{invoice_db_id}/comments", response_model=List[schemas.Comment])
def get_invoice_comments(invoice_db_id: int, db: Session = Depends(get_db)):
    """Retrieves all comments for a specific invoice."""
    return db.query(models.Comment).filter(models.Comment.invoice_id == invoice_db_id).order_by(models.Comment.created_at.asc()).all()

@router.post("/invoices/{invoice_db_id}/comments", response_model=schemas.Comment)
def add_invoice_comment(
    invoice_db_id: int,
    comment_in: schemas.CommentCreate,
    db: Session = Depends(get_db)
):
    """Adds a new internal comment to an invoice."""
    invoice = db.query(models.Invoice).filter(models.Invoice.id == invoice_db_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    db_comment = models.Comment(
        invoice_id=invoice_db_id,
        user=comment_in.user,
        text=comment_in.text,
        type="internal"
    )
    db.add(db_comment)
    log_audit_event(db, invoice_db_id=invoice_db_id, user=comment_in.user, action="Internal Comment Added", details={"comment": comment_in.text})
    db.commit()
    db.refresh(db_comment)
    return db_comment

@router.get("/invoices/{invoice_db_id}/audit-log", response_model=List[schemas.AuditLog])
def get_invoice_audit_log(invoice_db_id: int, db: Session = Depends(get_db)):
    """Retrieves the audit log for a specific invoice."""
    return db.query(models.AuditLog).filter(models.AuditLog.invoice_db_id == invoice_db_id).order_by(models.AuditLog.timestamp.desc()).all() 