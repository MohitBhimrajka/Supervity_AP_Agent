# src/app/core/background_tasks.py
from typing import List, Set, Dict, Any
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import contextmanager

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
    Process a single document in a worker thread.
    Returns (success, po_number, filename) tuple.
    """
    file_content = file_info["content"]
    filename = file_info["filename"]
    
    try:
        with get_thread_db_session() as db:
            # Process the document
            success, po_number = ingestion_service.ingest_document(
                db=db, 
                job_id=job_id,
                file_content=file_content,
                filename=filename
            )
            
            return success, po_number, filename
            
    except Exception as e:
        print(f"Error processing file {filename}: {e}")
        return False, None, filename

def update_job_progress(job_id: int, processed_count: int):
    """Helper function to update job progress in database."""
    try:
        with get_thread_db_session() as db:
            job = db.query(models.Job).filter_by(id=job_id).first()
            if job:
                job.processed_files = processed_count
                db.commit()
    except Exception as e:
        print(f"Error updating job progress: {e}")

def process_uploaded_documents(job_id: int, files_data: List[Dict[str, Any]]):
    """
    The main background task for processing a batch of uploaded files in parallel.
    Receives file content directly, not UploadFile objects.
    Uses configurable number of worker threads for parallel processing.
    """
    db = SessionLocal()
    job = db.query(models.Job).filter_by(id=job_id).first()
    if not job:
        print(f"Job ID {job_id} not found. Aborting task.")
        return

    try:
        # --- 1. Parallel Ingestion Phase ---
        print(f"Starting Parallel Ingestion Phase for Job ID: {job_id} with {PARALLEL_WORKERS} workers")
        print(f"Processing {len(files_data)} files...")
        
        affected_pos_set = set()
        
        # Process files in parallel with configured number of workers
        with ThreadPoolExecutor(max_workers=PARALLEL_WORKERS) as executor:
            # Submit all tasks
            futures = []
            for file_info in files_data:
                future = executor.submit(process_single_document, job_id, file_info)
                futures.append(future)
            
            # Wait for all tasks to complete and collect results
            successful_files = 0
            failed_files = 0
            processed_count = 0
            
            for future in as_completed(futures):
                try:
                    success, po_number, filename = future.result()
                    processed_count += 1
                    
                    if success:
                        successful_files += 1
                        if po_number:
                            affected_pos_set.add(po_number)
                        print(f"✅ Successfully processed: {filename}")
                    else:
                        failed_files += 1
                        print(f"❌ Failed to process: {filename}")
                    
                    # Update progress every 5 files or on the last file
                    if processed_count % 5 == 0 or processed_count == len(files_data):
                        update_job_progress(job_id, processed_count)
                        
                except Exception as e:
                    failed_files += 1
                    processed_count += 1
                    print(f"❌ Unexpected error in worker thread: {e}")
                    
                    # Still update progress for failed files
                    if processed_count % 5 == 0 or processed_count == len(files_data):
                        update_job_progress(job_id, processed_count)
        
        # Ensure final progress update
        update_job_progress(job_id, len(files_data))
        
        print(f"Parallel Ingestion Phase complete for Job ID: {job_id}")
        print(f"Results: {successful_files} successful, {failed_files} failed out of {len(files_data)} total files")
        print(f"POs to match: {list(affected_pos_set)} ({len(affected_pos_set)} unique POs)")

        # --- 2. Matching Phase ---
        print(f"Starting Matching Phase for Job ID: {job_id}")
        job.status = "matching"
        db.commit()

        # Matching can also be parallelized, but keeping it simple for now
        # since it's typically faster than document processing
        for po_number in affected_pos_set:
            matching_engine.run_match_for_po(db, po_number)
        
        # --- 3. Finalize Job ---
        job.status = "completed"
        job.completed_at = datetime.utcnow()
        job.summary = {
            "message": "Parallel processing and matching complete.",
            "affected_pos": list(affected_pos_set),
            "successful_files": successful_files,
            "failed_files": failed_files,
            "total_files": len(files_data)
        }
        db.commit()
        print(f"Job ID: {job_id} finalized successfully.")

    except Exception as e:
        print(f"A critical error occurred during background processing for Job ID {job_id}: {e}")
        if job:
            job.status = "failed"
            job.summary = {"error": str(e)}
            job.completed_at = datetime.utcnow()
            db.commit()
    finally:
        db.close() 