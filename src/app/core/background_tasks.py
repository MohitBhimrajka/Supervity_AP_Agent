# src/app/core/background_tasks.py
from typing import List, Set, Dict, Any
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import contextmanager
import re

from app.db.session import SessionLocal
from app.db import models
from app.modules.ingestion import service as ingestion_service
from app.modules.matching import engine as matching_engine
from app.config import PARALLEL_WORKERS

@contextmanager
def get_thread_db_session():
    """Context manager to provide thread-safe database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def process_single_document(job_id: int, file_info: Dict[str, Any]):
    """
    Process a single document.
    Returns a dictionary with detailed results for this file.
    """
    file_content = file_info["content"]
    filename = file_info["filename"]
    
    try:
        with get_thread_db_session() as db:
            success, affected_po_numbers, extracted_data = ingestion_service.ingest_document(
                db=db, 
                job_id=job_id,
                file_content=file_content,
                filename=filename
            )
            if success:
                doc_id = extracted_data.get('invoice_id') or extracted_data.get('grn_number') or extracted_data.get('po_number')
                return {
                    "filename": filename,
                    "status": "success",
                    "message": f"Successfully ingested as {extracted_data.get('document_type', 'Unknown')}",
                    "extracted_id": doc_id,
                    "affected_pos": affected_po_numbers
                }
            else:
                # Ingestion service now returns the error message
                error_message = extracted_data.get("error", "Extraction or validation failed.")
                return {
                    "filename": filename,
                    "status": "error",
                    "message": error_message,
                }
    except Exception as e:
        print(f"Critical error processing file {filename}: {e}")
        return {
            "filename": filename,
            "status": "error",
            "message": f"A system error occurred: {str(e)}",
        }

def update_job_progress(job_id: int, processed_count: int, status: str = "processing"):
    """Helper function to update job progress in database."""
    try:
        with get_thread_db_session() as db:
            job = db.query(models.Job).filter_by(id=job_id).first()
            if job:
                job.processed_files = processed_count
                job.status = status
                db.commit()
    except Exception as e:
        print(f"Error updating job progress: {e}")

def process_uploaded_documents(job_id: int, files_data: List[Dict[str, Any]]):
    """
    The main background task for processing a batch of uploaded files in parallel.
    Now processes POs first to prevent race conditions.
    """
    db = SessionLocal()
    job = db.query(models.Job).filter_by(id=job_id).first()
    if not job:
        print(f"Job ID {job_id} not found. Aborting task.")
        return

    try:
        print(f"Starting 3-Pass Ingestion for Job ID: {job_id}")
        all_results = []
        affected_pos_set = set()
        
        # --- START REWORKED 3-PASS LOGIC (WITH FIX) ---
        # Create mutually exclusive lists of files to process
        po_files = []
        grn_files = []
        invoice_files = []

        for f in files_data:
            filename = f.get("filename", "").upper()
            if "PO-" in filename:
                po_files.append(f)
            elif "GRN-" in filename:
                grn_files.append(f)
            else:
                invoice_files.append(f)
        
        processed_count = 0
        
        # Pass 1: Ingest Purchase Orders
        print(f"-> Pass 1: Processing {len(po_files)} Purchase Orders...")
        with ThreadPoolExecutor(max_workers=PARALLEL_WORKERS) as executor:
            futures = {executor.submit(process_single_document, job_id, file): file for file in po_files}
            for future in as_completed(futures):
                result = future.result()
                all_results.append(result)
                if result.get("status") == "success" and result.get("affected_pos"):
                    affected_pos_set.update(result["affected_pos"])
                processed_count += 1
                update_job_progress(job_id, processed_count)

        # Pass 2: Ingest Goods Receipt Notes
        print(f"-> Pass 2: Processing {len(grn_files)} GRNs...")
        with ThreadPoolExecutor(max_workers=PARALLEL_WORKERS) as executor:
            futures = {executor.submit(process_single_document, job_id, file): file for file in grn_files}
            for future in as_completed(futures):
                result = future.result()
                all_results.append(result)
                if result.get("status") == "success" and result.get("affected_pos"):
                    affected_pos_set.update(result["affected_pos"])
                processed_count += 1
                update_job_progress(job_id, processed_count)

        # Pass 3: Ingest Invoices and any remaining files
        print(f"-> Pass 3: Processing {len(invoice_files)} Invoices and others...")
        with ThreadPoolExecutor(max_workers=PARALLEL_WORKERS) as executor:
            futures = {executor.submit(process_single_document, job_id, file): file for file in invoice_files}
            for future in as_completed(futures):
                result = future.result()
                all_results.append(result)
                if result.get("status") == "success" and result.get("affected_pos"):
                    affected_pos_set.update(result["affected_pos"])
                processed_count += 1
                update_job_progress(job_id, processed_count)
        # --- END REWORKED 3-PASS LOGIC ---
        
        # --- 4. Matching Phase ---
        print(f"Starting Matching Phase for Job ID: {job_id}")
        update_job_progress(job_id, job.total_files, status="matching")

        invoices_to_match = db.query(models.Invoice).filter(models.Invoice.job_id == job_id).all()
        print(f"Found {len(invoices_to_match)} invoices from this job to match.")

        for invoice in invoices_to_match:
            try:
                matching_engine.run_match_for_invoice(db, invoice.id)
            except Exception as e:
                print(f"  [ERROR] Matching failed for Invoice ID {invoice.id}: {e}")
                invoice.status = models.DocumentStatus.needs_review
                invoice.match_trace = [{"step": "Engine Error", "status": "FAIL", "message": str(e)}]
                db.commit()
        
        # --- 5. Finalize Job ---
        job.status = "completed"
        job.completed_at = datetime.utcnow()
        job.summary = sorted(all_results, key=lambda x: x['filename']) # Sort results for consistency
        db.commit()
        print(f"Job ID: {job_id} finalized successfully.")

    except Exception as e:
        print(f"A critical error occurred during background processing for Job ID {job_id}: {e}")
        if job:
            job.status = "failed"
            job.summary = [{"filename": "System", "status": "error", "message": str(e)}]
            job.completed_at = datetime.utcnow()
            db.commit()
    finally:
        db.close() 