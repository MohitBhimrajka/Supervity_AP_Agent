# src/app/api/endpoints/documents.py
from fastapi import APIRouter, Depends, BackgroundTasks, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import os

from app.api.dependencies import get_db
from app.db import models, schemas
from app.core import background_tasks as tasks_service
# ADD THIS IMPORT
from app.modules.matching import engine as matching_engine
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
    Accepts multiple PDF files, reads them into memory, creates a job, 
    and starts a background task with the file data.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files were uploaded.")
    
    # Read files into memory before the request ends
    file_data_list: List[Dict[str, Any]] = []
    for file in files:
        file_data_list.append({
            "filename": file.filename,
            "content": await file.read()
        })
    
    # Create a new job record in the database
    job = models.Job(total_files=len(files))
    db.add(job)
    db.commit()
    db.refresh(job)

    # Pass the file data, not the closed file objects
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
    Searches for invoices with a dynamic set of filters.
    Supports flexible filtering on any invoice field with various operators.
    """
    query = db.query(models.Invoice)
    
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
        
            return query.order_by(models.Invoice.invoice_date.desc()).all()


# ADD THIS NEW ENDPOINT
@router.put("/purchase-orders/{po_db_id}")
def update_purchase_order(
    po_db_id: int, 
    changes: Dict[str, Any],
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Updates a Purchase Order's details and triggers a re-match for all
    related invoices.
    """
    po = db.query(models.PurchaseOrder).options(
        joinedload(models.PurchaseOrder.invoices)
    ).filter(models.PurchaseOrder.id == po_db_id).first()

    if not po:
        raise HTTPException(status_code=404, detail="Purchase Order not found")

    # Update the PO object
    for key, value in changes.items():
        if hasattr(po, key):
            setattr(po, key, value)
    
    # Also update the raw_data_payload to ensure PDF regeneration is accurate
    if po.raw_data_payload:
        for key, value in changes.items():
            if key in po.raw_data_payload:
                po.raw_data_payload[key] = value

    # Log the action
    audit_log = models.AuditLog(
        entity_type='PurchaseOrder',
        entity_id=str(po.id),
        user='System', # Should be replaced with actual user from auth
        action='Updated from Workbench',
        details={'changes': changes}
    )
    db.add(audit_log)
    
    # Find all related invoices to rematch
    invoices_to_rematch = po.invoices
    
    db.commit() # Commit the PO changes first
    
    # Trigger a background task to re-run matching for all affected invoices
    for inv in invoices_to_rematch:
        background_tasks.add_task(matching_engine.run_match_for_invoice, db, inv.id)

    db.refresh(po)
    return {"message": "Purchase Order updated. Rematching related invoices in the background.", "po": schemas.PurchaseOrder.from_orm(po)} 