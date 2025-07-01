# src/app/api/endpoints/documents.py
from fastapi import APIRouter, Depends, BackgroundTasks, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session, Query
from typing import List, Dict, Any
import os
import io
import csv
import glob

from app.api.dependencies import get_db
from app.db import models, schemas
from app.core import background_tasks as tasks_service
# ADD THIS IMPORT
from app.modules.matching import engine as matching_engine
from app.utils.auditing import log_audit_event
from sqlalchemy.orm import joinedload

router = APIRouter()

# This should be the path to the directory where you generate/upload PDFs
# Make sure it's accessible from your backend's running location.
PDF_STORAGE_PATH = "sample_data/arcelormittal_documents"
GENERATED_PDF_STORAGE_PATH = "generated_documents"

@router.get("/file/{filename}")
def get_document_file(filename: str):
    """Serves a document PDF file for the frontend viewer."""
    
    # Check in the primary data directory first
    filepath = os.path.join(PDF_STORAGE_PATH, filename)
    if os.path.exists(filepath):
        return FileResponse(filepath)
        
    # Check in the generated documents directory as a fallback
    filepath = os.path.join(GENERATED_PDF_STORAGE_PATH, filename)
    if os.path.exists(filepath):
        return FileResponse(filepath)
        
    raise HTTPException(status_code=404, detail="File not found")

@router.post("/upload", response_model=schemas.Job, status_code=202)
async def upload_documents(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    """
    Accepts multiple PDF files, SAVES THEM TO DISK, creates a job, 
    and starts a background task with the file data.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files were uploaded.")
    
    # Ensure the upload directory exists
    os.makedirs(PDF_STORAGE_PATH, exist_ok=True)
    
    file_data_list: List[Dict[str, Any]] = []
    for file in files:
        # Read content into memory first to pass to background task
        content = await file.read()
        
        # Define the file path and save the file to disk
        file_path = os.path.join(PDF_STORAGE_PATH, file.filename)
        with open(file_path, "wb") as buffer:
            buffer.write(content)
        
        # Add to the list for the background task
        file_data_list.append({
            "filename": file.filename,
            "content": content
        })
    
    # Create a new job record in the database
    job = models.Job(total_files=len(files))
    db.add(job)
    db.commit()
    db.refresh(job)

    # Pass the file data, not the closed file objects
    background_tasks.add_task(tasks_service.process_uploaded_documents, job.id, file_data_list)
    
    return job

@router.post("/sync-sample-data", response_model=schemas.Job, status_code=202)
async def sync_sample_data(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Finds all PDFs in the sample data directory, creates a job,
    and processes them in the background. Simulates a sync from an external source.
    """
    sample_files = glob.glob(os.path.join(PDF_STORAGE_PATH, "*.pdf"))
    if not sample_files:
        raise HTTPException(status_code=404, detail="No sample PDF files found in the directory.")

    file_data_list: List[Dict[str, Any]] = []
    for file_path in sample_files:
        with open(file_path, "rb") as f:
            file_data_list.append({
                "filename": os.path.basename(file_path),
                "content": f.read()
            })
    
    job = models.Job(total_files=len(file_data_list))
    db.add(job)
    db.commit()
    db.refresh(job)

    background_tasks.add_task(tasks_service.process_uploaded_documents, job.id, file_data_list)
    
    return job

@router.get("/jobs/{job_id}", response_model=schemas.Job)
def get_job_status(job_id: int, db: Session = Depends(get_db)):
    """
    Allows the frontend to poll for the status of a processing job.
    """
    job = db.query(models.Job).filter(models.Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job ID not found")
    return job

@router.get("/jobs", response_model=List[schemas.Job])
def get_all_jobs(limit: int = 20, db: Session = Depends(get_db)):
    """
    Allows the frontend to get a list of recent processing jobs.
    """
    return db.query(models.Job).order_by(models.Job.created_at.desc()).limit(limit).all()

@router.post("/search", response_model=List[schemas.Invoice])
def search_invoices_flexible(request: schemas.SearchRequest, db: Session = Depends(get_db)):
    """
    Searches for invoices with a dynamic set of filters and sorting options.
    """
    query: Query = db.query(models.Invoice)  # Add type hint for clarity
    
    for condition in request.filters:
        column = getattr(models.Invoice, condition.field, None)
        if column is None:
            # Skip invalid field names to avoid errors
            continue

        if condition.operator == 'is' or condition.operator == 'equals':
            query = query.filter(column == condition.value)
        elif condition.operator == 'contains':
            # Use case-insensitive LIKE for string fields
            query = query.filter(column.ilike(f"%{condition.value}%"))
        elif condition.operator == 'gt':
            query = query.filter(column > condition.value)
        elif condition.operator == 'lt':
            query = query.filter(column < condition.value)
        elif condition.operator == 'gte':
            query = query.filter(column >= condition.value)
        elif condition.operator == 'lte':
            query = query.filter(column <= condition.value)
        elif condition.operator == 'not_equals':
            query = query.filter(column != condition.value)
        elif condition.operator == 'in':
            # For checking if value is in a list
            if isinstance(condition.value, list):
                query = query.filter(column.in_(condition.value))
        elif condition.operator == 'not_in':
            # For checking if value is not in a list
            if isinstance(condition.value, list):
                query = query.filter(~column.in_(condition.value))
        elif condition.operator == 'is_null':
            query = query.filter(column.is_(None))
        elif condition.operator == 'is_not_null':
            query = query.filter(column.isnot(None))
        # Add more operators as needed

    # --- ADD SORTING LOGIC ---
    sort_column = getattr(models.Invoice, request.sort_by, models.Invoice.invoice_date)
    if request.sort_order == 'asc':
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())
        
    return query.all()  # Remove limit, frontend will handle pagination if needed


# ADD THIS NEW ENDPOINT
@router.post("/export-csv")
def export_invoices_to_csv(request: schemas.SearchRequest, db: Session = Depends(get_db)):
    """
    Exports invoices to a CSV file based on the provided search filters.
    """
    # Reuse the same search logic to get the filtered invoices
    query: Query = db.query(models.Invoice)
    
    for condition in request.filters:
        column = getattr(models.Invoice, condition.field, None)
        if column is None:
            continue

        if condition.operator == 'is' or condition.operator == 'equals':
            query = query.filter(column == condition.value)
        elif condition.operator == 'contains':
            query = query.filter(column.ilike(f"%{condition.value}%"))
        elif condition.operator == 'gt':
            query = query.filter(column > condition.value)
        elif condition.operator == 'lt':
            query = query.filter(column < condition.value)
        elif condition.operator == 'gte':
            query = query.filter(column >= condition.value)
        elif condition.operator == 'lte':
            query = query.filter(column <= condition.value)
        elif condition.operator == 'not_equals':
            query = query.filter(column != condition.value)
        elif condition.operator == 'in':
            if isinstance(condition.value, list):
                query = query.filter(column.in_(condition.value))
        elif condition.operator == 'not_in':
            if isinstance(condition.value, list):
                query = query.filter(~column.in_(condition.value))
        elif condition.operator == 'is_null':
            query = query.filter(column.is_(None))
        elif condition.operator == 'is_not_null':
            query = query.filter(column.isnot(None))

    # Apply sorting
    sort_column = getattr(models.Invoice, request.sort_by, models.Invoice.invoice_date)
    if request.sort_order == 'asc':
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())
    
    invoices = query.all()

    output = io.StringIO()
    writer = csv.writer(output)

    # Write header
    header = [
        'invoice_id', 'vendor_name', 'invoice_date', 'due_date', 'status',
        'subtotal', 'tax', 'grand_total', 'related_po_numbers'
    ]
    writer.writerow(header)

    # Write rows
    for inv in invoices:
        writer.writerow([
            inv.invoice_id,
            inv.vendor_name,
            inv.invoice_date,
            inv.due_date,
            inv.status.value,
            inv.subtotal,
            inv.tax,
            inv.grand_total,
            ", ".join(inv.related_po_numbers) if inv.related_po_numbers else ""
        ])

    output.seek(0)
    
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode('utf-8')),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=invoice_export.csv"}
    )


@router.put("/purchase-orders/{po_db_id}")
def update_purchase_order(
    po_db_id: int, 
    changes: Dict[str, Any],
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Updates a Purchase Order's details and triggers a re-match for all
    related invoices. Includes server-side validation and detailed auditing.
    """
    po = db.query(models.PurchaseOrder).options(
        joinedload(models.PurchaseOrder.invoices)
    ).filter(models.PurchaseOrder.id == po_db_id).first()

    if not po:
        raise HTTPException(status_code=404, detail="Purchase Order not found")

    # --- NEW VALIDATION LOGIC ---
    if 'line_items' in changes:
        for item in changes['line_items']:
            # Ensure ordered_qty is a non-negative number
            if 'ordered_qty' in item and (not isinstance(item['ordered_qty'], (int, float)) or item['ordered_qty'] < 0):
                raise HTTPException(status_code=400, detail=f"Invalid quantity for item '{item.get('description', 'Unknown')}'. Must be a positive number.")
            # Ensure unit_price is a non-negative number
            if 'unit_price' in item and (not isinstance(item['unit_price'], (int, float)) or item['unit_price'] < 0):
                raise HTTPException(status_code=400, detail=f"Invalid price for item '{item.get('description', 'Unknown')}'. Must be a positive number.")
    
    # Validate grand_total if provided
    if 'grand_total' in changes and (not isinstance(changes['grand_total'], (int, float)) or changes['grand_total'] < 0):
        raise HTTPException(status_code=400, detail="Invalid grand total. Must be a positive number.")
    
    # Validate subtotal if provided
    if 'subtotal' in changes and (not isinstance(changes['subtotal'], (int, float)) or changes['subtotal'] < 0):
        raise HTTPException(status_code=400, detail="Invalid subtotal. Must be a positive number.")
    
    # Validate tax if provided
    if 'tax' in changes and (not isinstance(changes['tax'], (int, float)) or changes['tax'] < 0):
        raise HTTPException(status_code=400, detail="Invalid tax amount. Must be a positive number.")
    # --- END VALIDATION LOGIC ---

    # Update the PO object
    for key, value in changes.items():
        if hasattr(po, key):
            setattr(po, key, value)
    
    # Also update the raw_data_payload to ensure PDF regeneration is accurate
    if po.raw_data_payload:
        for key, value in changes.items():
            if key in po.raw_data_payload:
                po.raw_data_payload[key] = value

    invoices_to_rematch = po.invoices
    
    # Create a simple diff summary for the audit log
    summary_parts = []
    if 'line_items' in changes:
        # A more sophisticated diff could be done here, but for now, this is clear
        summary_parts.append(f"Updated {len(changes['line_items'])} line item(s).")
    other_changes = {k: v for k, v in changes.items() if k != 'line_items'}
    if other_changes:
        summary_parts.append(f"Updated fields: {', '.join(other_changes.keys())}.")
    
    update_summary = " ".join(summary_parts) if summary_parts else "No specific changes detailed."

    # Log the audit event for each affected invoice before committing
    for inv in invoices_to_rematch:
        log_audit_event(
            db,
            invoice_db_id=inv.id,
            user='AP Team',
            action='PO Updated, Triggering Rematch',
            summary=f"PO {po.po_number} was updated. {update_summary}",
            details={'po_number': po.po_number, 'changes': changes}
        )
    
    db.commit() # Commit PO changes and audit logs together
    
    # Trigger background re-match for all affected invoices
    for inv in invoices_to_rematch:
        print(f"Queueing invoice ID {inv.id} for re-matching due to PO update.")
        # Pass only the ID to the background task
        background_tasks.add_task(matching_engine.run_match_for_invoice, db, inv.id)

    db.refresh(po)
    # Return a success message. The frontend will poll for the new status.
    return {"message": "Purchase Order updated. Rematching related invoices in the background."}


@router.get("/jobs/{job_id}/invoices", response_model=List[schemas.Invoice])
def get_invoices_for_job(job_id: int, db: Session = Depends(get_db)):
    """
    Retrieves the invoice objects that were created as part of a specific job.
    Used by the Data Center to show the result of an upload.
    """
    job = db.query(models.Job).filter(models.Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job ID not found")
    
    invoices = db.query(models.Invoice).filter(models.Invoice.job_id == job_id).all()
    if not invoices:
        # This can happen if the uploaded file was not an invoice or failed extraction
        return []
        
    return invoices 