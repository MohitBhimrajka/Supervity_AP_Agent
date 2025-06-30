# src/app/api/endpoints/invoices.py
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import math

from app.api.dependencies import get_db
from app.db import models, schemas
from app.utils import data_formatting
# ADD THIS NEW IMPORT
from app.modules.matching import comparison as comparison_service
from app.modules.matching import engine as matching_engine
from app.utils.auditing import log_audit_event
from pydantic import BaseModel

router = APIRouter()

# ADD THIS SCHEMA FOR THE REQUEST BODY
class UpdateNoteRequest(BaseModel):
    notes: str

class UpdateGLCodeRequest(BaseModel):
    gl_code: str

# ADD THIS NEW SCHEMA
class BatchUpdateStatusRequest(BaseModel):
    invoice_ids: List[int]  # List of database IDs
    new_status: str
    reason: Optional[str] = "Bulk update via Invoice Explorer"

class BatchMarkAsPaidRequest(BaseModel):
    invoice_ids: List[int]

@router.get("/", response_model=List[schemas.InvoiceSummary])
def get_invoices(status: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Gets a list of invoices, filterable by status.
    Uses a lightweight summary schema for efficiency.
    """
    query = db.query(models.Invoice)
    if status:
        try:
            # Handle empty status string from frontend calls
            if status.strip():
                status_enum = models.DocumentStatus(status)
                query = query.filter(models.Invoice.status == status_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status value: {status}")
            
    return query.order_by(models.Invoice.invoice_date.desc()).all()


@router.get("/{invoice_id}/details")
def get_invoice_details(invoice_id: str, db: Session = Depends(get_db)):
    """
    Retrieves all linked information for a single invoice.
    This is a raw data endpoint, for a more user-friendly version use /dossier.
    """
    invoice = db.query(models.Invoice).filter(models.Invoice.invoice_id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    po = None
    # Find PO through GRN first
    if invoice.grn and invoice.grn.po:
        po = invoice.grn.po
    # Fallback to direct PO link on invoice if no GRN link
    elif invoice.po_number:
        po = db.query(models.PurchaseOrder).filter(models.PurchaseOrder.po_number == invoice.po_number).first()


    response = {
        "invoice": schemas.Invoice.from_orm(invoice),
        "grn": schemas.GoodsReceiptNote.from_orm(invoice.grn) if invoice.grn else None,
        "po": schemas.PurchaseOrder.from_orm(po) if po else None
    }
    return response

@router.post("/{invoice_id}/update-status")
def update_invoice_status_endpoint(
    invoice_id: str,
    request: schemas.UpdateInvoiceStatusRequest,
    db: Session = Depends(get_db)
):
    """
    Endpoint to update an invoice's status (e.g., approve, reject, pay).
    Now sets paid_date when status is updated to 'paid'.
    """
    invoice = db.query(models.Invoice).filter(models.Invoice.invoice_id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    try:
        new_status_enum = models.DocumentStatus(request.new_status)
    except ValueError:
        valid_statuses = [s.value for s in models.DocumentStatus]
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status '{request.new_status}'. Valid statuses are: {valid_statuses}"
        )

    old_status = invoice.status
    invoice.status = new_status_enum
    
    # NEW: Set paid_date when moving to 'paid' status
    if new_status_enum == models.DocumentStatus.paid:
        invoice.paid_date = datetime.utcnow().date()
    
    # THE LEARNING TRIGGER: If an invoice that needed review is now approved, learn from it.
    if old_status == models.DocumentStatus.needs_review and new_status_enum == models.DocumentStatus.matched:
        print(f"🧠 Learning from manual approval of invoice {invoice.invoice_id}...")
        _learn_from_manual_approval(db, invoice)
    
    # Create an audit log entry
    audit_log = models.AuditLog(
        entity_type='Invoice',
        entity_id=invoice.invoice_id,
        user='System', # In a real app, this would be the logged-in user
        action='Status Changed',
        details={'from': old_status.value, 'to': new_status_enum.value, 'reason': request.reason}
    )
    db.add(audit_log)

    db.commit()
    return {"message": f"Invoice {invoice_id} status updated to '{request.new_status}' successfully."}

@router.get("/{invoice_id}/dossier")
def get_invoice_dossier(invoice_id: str, db: Session = Depends(get_db)):
    """
    Retrieves and formats a complete "dossier" for an invoice, including all
    related documents (PO, GRN), their raw data, and file paths for display.
    This is the primary endpoint for viewing a document and its context.
    """
    invoice = db.query(models.Invoice).filter(models.Invoice.invoice_id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    # The formatting logic is now more complex and lives in the data_formatting utility
    formatted_dossier = data_formatting.format_full_dossier(invoice, db)
    
    return formatted_dossier

def _learn_from_manual_approval(db: Session, invoice: models.Invoice):
    """
    Analyzes a manually approved invoice to create or update a LearnedHeuristic.
    This now reads from the match_trace field.
    """
    # We only learn from invoices that have a match trace
    if not invoice.match_trace or not invoice.vendor_name:
        return

    # Find the first failed step in the trace to learn from
    first_failure = next((step for step in invoice.match_trace if step.get("status") == "FAIL"), None)

    if not first_failure:
        return # No failure to learn from
    
    failure_details = first_failure.get("details", {})
    failure_step = first_failure.get("step", "")
    
    learned_condition = {}
    exception_type = "" # We'll derive this from the step name

    if "Price Match" in failure_step:
        exception_type = "PriceMismatchException"
        invoice_price = failure_details.get("invoice_price", 0)
        po_price = failure_details.get("po_price", 0)
        if po_price > 0:
            variance = abs(invoice_price - po_price) / po_price * 100
            learned_condition = {"max_variance_percent": math.ceil(variance)}
    elif "Quantity Match" in failure_step:
        exception_type = "QuantityMismatchException"
        invoice_qty = failure_details.get("invoice_qty", 0)
        # Check if it was compared to GRN or PO
        grn_qty = failure_details.get("grn_qty")
        po_qty = failure_details.get("po_qty")
        if grn_qty is not None:
             learned_condition = {"max_quantity_diff": abs(invoice_qty - grn_qty)}
        elif po_qty is not None:
             learned_condition = {"max_quantity_diff": abs(invoice_qty - po_qty)}

    if not exception_type or not learned_condition:
        return # Could not determine a learnable condition

    # Check if a similar heuristic already exists
    heuristic = db.query(models.LearnedHeuristic).filter_by(
        vendor_name=invoice.vendor_name,
        exception_type=exception_type,
        learned_condition=learned_condition
    ).first()

    if heuristic:
        # If it exists, strengthen it
        heuristic.trigger_count += 1
        # Confidence formula: approaches 1 as trigger_count increases
        heuristic.confidence_score = 1.0 - (1.0 / (heuristic.trigger_count + 1))
        print(f"✅ Strengthened heuristic for {invoice.vendor_name}: {exception_type}. New confidence: {heuristic.confidence_score:.2f}")
    else:
        # If not, create a new one
        new_heuristic = models.LearnedHeuristic(
            vendor_name=invoice.vendor_name,
            exception_type=exception_type,
            learned_condition=learned_condition,
            resolution_action=models.DocumentStatus.matched.value,
            trigger_count=1,
            confidence_score=0.5 # Start with a moderate confidence for a new rule
        )
        db.add(new_heuristic)
        print(f"✅ Created new heuristic for {invoice.vendor_name}: {exception_type}")


# ADD THIS ENTIRE NEW ENDPOINT AT THE END OF THE FILE
@router.get("/{invoice_db_id}/comparison-data")
def get_invoice_comparison_data(invoice_db_id: int, db: Session = Depends(get_db)):
    """
    Retrieves and prepares all data needed for the interactive workbench
    comparison view for a single invoice.
    """
    data = comparison_service.prepare_comparison_data(db, invoice_db_id)
    if "error" in data:
        raise HTTPException(status_code=404, detail=data["error"])
    return data

# ADD THIS NEW ENDPOINT
@router.put("/{invoice_db_id}/notes")
def update_invoice_notes(
    invoice_db_id: int,
    request: UpdateNoteRequest,
    db: Session = Depends(get_db)
):
    """Updates the notes field for a given invoice."""
    invoice = db.query(models.Invoice).filter(models.Invoice.id == invoice_db_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    invoice.notes = request.notes
    
    # Log the audit event with summary
    log_audit_event(
        db, 
        invoice.id, 
        "AP Team", 
        "Reference Notes Updated", 
        summary=f"Notes updated: '{request.notes[:50]}{'...' if len(request.notes) > 50 else ''}'"
    )
    
    db.commit()
    
    return {"message": "Notes updated successfully."}

@router.put("/{invoice_db_id}/gl-code")
def update_invoice_gl_code(
    invoice_db_id: int,
    request: UpdateGLCodeRequest,
    db: Session = Depends(get_db)
):
    """Updates the GL code for a given invoice."""
    invoice = db.query(models.Invoice).filter(models.Invoice.id == invoice_db_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    invoice.gl_code = request.gl_code
    
    # Log the action using the utility with summary
    log_audit_event(
        db, 
        invoice.id, 
        "AP Team", 
        "GL Code Applied", 
        summary=f"GL Code set to '{request.gl_code}'.",
        details={'gl_code': request.gl_code}
    )
    
    db.commit()
    
    return {"message": "GL Code updated successfully."}


# ADD THIS NEW ENDPOINT AT THE END OF THE FILE
@router.post("/batch-update-status")
def batch_update_invoice_status(
    request: BatchUpdateStatusRequest,
    db: Session = Depends(get_db)
):
    """Updates the status for a list of invoices."""
    if not request.invoice_ids:
        raise HTTPException(status_code=400, detail="No invoice IDs provided.")
    
    try:
        new_status_enum = models.DocumentStatus(request.new_status)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid status value: {request.new_status}")

    query = db.query(models.Invoice).filter(models.Invoice.id.in_(request.invoice_ids))
    
    updated_count = 0
    for invoice in query.all():
        old_status = invoice.status
        invoice.status = new_status_enum
        
        # Set paid_date when moving to 'paid' status
        if new_status_enum == models.DocumentStatus.paid:
            invoice.paid_date = datetime.utcnow().date()
        
        # Log each change
        audit_log = models.AuditLog(
            entity_type='Invoice',
            entity_id=invoice.invoice_id,
            user='System',  # Should be replaced with actual user from auth
            action='Status Changed (Bulk)',
            details={'from': old_status.value, 'to': new_status_enum.value, 'reason': request.reason}
        )
        db.add(audit_log)
        updated_count += 1
    
    db.commit()

    return {
        "message": f"Successfully updated {updated_count} of {len(request.invoice_ids)} invoices to '{request.new_status}'.",
        "updated_count": updated_count
    }

@router.post("/batch-mark-as-paid")
def batch_mark_as_paid(
    request: BatchMarkAsPaidRequest,
    db: Session = Depends(get_db)
):
    """Marks a list of invoices with status 'pending_payment' as 'paid'."""
    if not request.invoice_ids:
        raise HTTPException(status_code=400, detail="No invoice IDs provided.")
    
    query = db.query(models.Invoice).filter(
        models.Invoice.id.in_(request.invoice_ids),
        models.Invoice.status == models.DocumentStatus.pending_payment
    )
    
    updated_count = 0
    for invoice in query.all():
        invoice.status = models.DocumentStatus.paid
        invoice.paid_date = datetime.utcnow().date()
        
        audit_log = models.AuditLog(
            entity_type='Invoice', entity_id=invoice.invoice_id, user='System',
            action='Payment Confirmed (Bulk)', details={'batch_id': invoice.payment_batch_id}
        )
        db.add(audit_log)
        updated_count += 1
    
    db.commit()

    if updated_count == 0:
        raise HTTPException(status_code=404, detail="No valid invoices in 'pending_payment' status were found for the given IDs.")

    return {
        "message": f"Successfully marked {updated_count} invoice(s) as paid.",
        "updated_count": updated_count
    }

@router.get("/by-category", response_model=List[schemas.InvoiceSummary])
def get_invoices_by_category(category: str, db: Session = Depends(get_db)):
    """Retrieves all invoices in review for a specific category."""
    return db.query(models.Invoice).filter(
        models.Invoice.status == models.DocumentStatus.needs_review,
        models.Invoice.review_category == category
    ).order_by(models.Invoice.invoice_date.desc()).all()

@router.post("/batch-rematch", status_code=202)
def batch_rematch_invoices(
    request: schemas.BatchActionRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Triggers a re-match for a list of invoices."""
    if not request.invoice_ids:
        raise HTTPException(status_code=400, detail="No invoice IDs provided.")

    invoices = db.query(models.Invoice).filter(models.Invoice.id.in_(request.invoice_ids)).all()
    
    rematched_count = 0
    for inv in invoices:
        # Change status to 'matching' immediately for better UX
        inv.status = models.DocumentStatus.matching
        log_audit_event(
            db=db, 
            invoice_db_id=inv.id, 
            user="AP Team", 
            action="Manual Rematch Triggered", 
            summary="Rematch triggered from Invoice Explorer.",
            details={"source": "Invoice Explorer"}
        )
        background_tasks.add_task(matching_engine.run_match_for_invoice, db, inv.id)
        rematched_count += 1
    
    db.commit()

    return {
        "message": f"Successfully queued {rematched_count} invoice(s) for re-matching.",
        "rematched_count": rematched_count
    }

@router.get("/by-string-id/{invoice_id_str:path}", response_model=schemas.InvoiceSummary)
def get_invoice_by_string_id(invoice_id_str: str, db: Session = Depends(get_db)):
    """
    Retrieves a single invoice's summary data using its string-based ID.
    The ":path" converter allows the ID to contain slashes.
    """
    invoice = db.query(models.Invoice).filter(models.Invoice.invoice_id == invoice_id_str).first()
    if not invoice:
        raise HTTPException(status_code=404, detail=f"Invoice with ID '{invoice_id_str}' not found.")
    return invoice