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
    """Processes a single document and returns its DB ID if it's an invoice."""
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
                invoice_db_id = None
                if extracted_data.get('document_type') == 'Invoice':
                    # Get the ID of the newly created invoice
                    inv_obj = db.query(models.Invoice.id).filter_by(invoice_id=extracted_data.get('invoice_id')).scalar()
                    invoice_db_id = inv_obj
                return {
                    "filename": filename,
                    "status": "success",
                    "message": f"Successfully ingested as {extracted_data.get('document_type', 'Unknown')}",
                    "extracted_id": doc_id,
                    "affected_pos": affected_po_numbers,
                    "invoice_db_id": invoice_db_id
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
    Orchestrates ingestion and then triggers the matching phase.
    """
    db = SessionLocal()
    job = db.query(models.Job).filter_by(id=job_id).first()
    if not job:
        print(f"Job ID {job_id} not found. Aborting task.")
        return

    try:
        print(f"Starting Ingestion for Job ID: {job_id}")
        all_results = []
        affected_pos_set = set()
        invoice_ids_to_match = []
        
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
                if result.get("status") == "success" and result.get("invoice_db_id"):
                    invoice_ids_to_match.append(result["invoice_db_id"])
                processed_count += 1
                update_job_progress(job_id, processed_count)
        # --- END REWORKED 3-PASS LOGIC ---
        
        # --- NEW Matching Phase ---
        print(f"Ingestion complete. Queueing {len(invoice_ids_to_match)} invoices for matching.")
        update_job_progress(job_id, job.total_files, status="matching")

        for inv_id in invoice_ids_to_match:
            try:
                # We can call this directly since it's in a background task context
                matching_engine.run_match_for_invoice(db, inv_id)
            except Exception as e:
                print(f"  [ERROR] Matching failed for Invoice ID {inv_id}: {e}")
                inv = db.query(models.Invoice).filter(models.Invoice.id == inv_id).first()
                if inv:
                    inv.status = models.DocumentStatus.needs_review
                    inv.match_trace = [{"step": "Engine Error", "status": "FAIL", "message": str(e)}]
                    db.commit()
        
        job.status = "completed"
        job.completed_at = datetime.utcnow()
        job.summary = sorted(all_results, key=lambda x: x['filename'])
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