# src/app/api/endpoints/payments.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from datetime import datetime

from app.api.dependencies import get_db
from app.db import models, schemas

router = APIRouter()

class CreatePaymentBatchRequest(BaseModel):
    invoice_ids: List[int] # List of invoice database IDs

@router.get("/payable", response_model=List[schemas.Invoice])
def get_payable_invoices(db: Session = Depends(get_db)):
    """Retrieves all invoices with status 'approved_for_payment'."""
    return db.query(models.Invoice).filter(
        models.Invoice.status == models.DocumentStatus.approved_for_payment
    ).order_by(models.Invoice.due_date.asc()).all()

@router.post("/batches", status_code=201)
def create_payment_batch(
    request: CreatePaymentBatchRequest,
    db: Session = Depends(get_db)
):
    """
    Creates a payment batch from a list of invoice IDs.
    This updates their status to 'pending_payment'.
    """
    if not request.invoice_ids:
        return {"error": "No invoice IDs provided."}

    invoices = db.query(models.Invoice).filter(
        models.Invoice.id.in_(request.invoice_ids),
        models.Invoice.status == models.DocumentStatus.approved_for_payment
    ).all()

    if len(invoices) != len(request.invoice_ids):
        # This indicates some IDs were invalid or not in the correct status
        print("Warning: Mismatch in provided invoice IDs and valid payable invoices.")

    batch_id = f"PAY-BATCH-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    total_amount = 0
    
    for inv in invoices:
        inv.status = models.DocumentStatus.pending_payment
        total_amount += inv.grand_total or 0
        
        # Log the action
        audit_log = models.AuditLog(
            entity_type='Invoice', entity_id=inv.invoice_id, user='System', # Should be a real user
            action='Added to Payment Batch', details={"batch_id": batch_id}
        )
        db.add(audit_log)

    db.commit()

    return {
        "message": "Payment batch created successfully.",
        "batch_id": batch_id,
        "processed_invoice_count": len(invoices),
        "total_amount": total_amount,
    } 