# src/app/api/endpoints/payments.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from datetime import datetime

from app.api.dependencies import get_db
from app.db import models, schemas
from app.utils.auditing import log_audit_event

router = APIRouter()

class CreatePaymentBatchRequest(BaseModel):
    invoice_ids: List[int] # List of invoice database IDs

@router.get("/payable", response_model=List[schemas.InvoiceSummary])
def get_payable_invoices(db: Session = Depends(get_db)):
    """Retrieves all invoices with status 'matched'."""
    return db.query(models.Invoice).filter(
        models.Invoice.status == models.DocumentStatus.matched
    ).order_by(models.Invoice.due_date.asc()).all()

@router.post("/batches", status_code=201)
def create_payment_batch(
    request: CreatePaymentBatchRequest,
    db: Session = Depends(get_db)
):
    """
    Creates a payment batch from a list of 'matched' invoice IDs, updates their status
    to 'pending_payment', and stamps them with a unique batch ID.
    """
    if not request.invoice_ids:
        raise HTTPException(status_code=400, detail="No invoice IDs provided.")

    invoices = db.query(models.Invoice).filter(
        models.Invoice.id.in_(request.invoice_ids),
        models.Invoice.status == models.DocumentStatus.matched
    ).all()

    if len(invoices) != len(request.invoice_ids):
        raise HTTPException(status_code=400, detail="One or more invoices were not in 'matched' status or did not exist.")

    if not invoices:
        raise HTTPException(status_code=400, detail="No valid invoices found to create a batch.")

    batch_id = f"PAY-BATCH-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    total_amount = 0
    
    for inv in invoices:
        inv.status = models.DocumentStatus.pending_payment
        inv.payment_batch_id = batch_id
        total_amount += inv.grand_total or 0
        
        log_audit_event(
            db=db, invoice_db_id=inv.id, user='System',
            action='Added to Payment Batch', details={"batch_id": batch_id}
        )

    db.commit()

    return {
        "message": f"Payment batch {batch_id} created successfully.",
        "batch_id": batch_id,
        "processed_invoice_count": len(invoices),
        "total_amount": total_amount,
    } 