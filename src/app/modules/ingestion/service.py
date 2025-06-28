# src/app/modules/ingestion/service.py
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Dict, Tuple

from app.db import models, schemas
from app.modules.ingestion import extractor

def ingest_document(db: Session, job_id: int, file_content: bytes, filename: str) -> Tuple[bool, str | None]:
    """
    Orchestrates the ingestion of a single document.
    1. Extracts data using the extractor.
    2. Saves the data and the original filename to the database.
    3. Returns success status and the document's primary PO number.
    """
    print(f"--- Ingesting file: {filename} for Job ID: {job_id} ---")
    
    extracted_data = extractor.extract_data_from_pdf(file_content)
    if not extracted_data:
        print(f"Data extraction failed for {filename}. Skipping.")
        return False, None
        
    doc_type = extracted_data.get("document_type")
    if not doc_type:
        print(f"Could not determine document type for {filename}. Skipping.")
        return False, None
        
    primary_po_number = None
    try:
        if doc_type == "Purchase Order":
            # --- FIX START ---
            po_create = schemas.PurchaseOrderCreate(**extracted_data)
            # Save the full extracted data as the raw payload
            db_po = models.PurchaseOrder(**po_create.model_dump(), file_path=filename, raw_data_payload=extracted_data)
            # --- FIX END ---
            db.add(db_po)
            primary_po_number = db_po.po_number
        elif doc_type == "Goods Receipt Note":
            grn_create = schemas.GoodsReceiptNoteCreate(**extracted_data)
            db_grn = models.GoodsReceiptNote(**grn_create.model_dump(), file_path=filename)
            db.add(db_grn)
            primary_po_number = db_grn.po_number
        elif doc_type == "Invoice":
            invoice_create = schemas.InvoiceCreate(**extracted_data)
            db_invoice = models.Invoice(**invoice_create.model_dump(), job_id=job_id, file_path=filename)
            db.add(db_invoice)
            if db_invoice.grn_number:
                grn = db.query(models.GoodsReceiptNote).filter_by(grn_number=db_invoice.grn_number).first()
                if grn:
                    primary_po_number = grn.po_number
                else:
                    primary_po_number = db_invoice.po_number
            else:
                primary_po_number = db_invoice.po_number
        else:
            print(f"Unknown document type '{doc_type}' for {filename}. Skipping.")
            return False, None
        
        db.commit()
        print(f"Successfully saved {doc_type} from {filename} to database.")
        return True, primary_po_number

    except IntegrityError as e:
        db.rollback()
        print(f"Database integrity error for {filename}: {e}. This is likely a duplicate. Skipping.")
        # Attempt to get the PO number even on duplicates for matching purposes
        primary_po_number = extracted_data.get("po_number")
        return False, primary_po_number
    except Exception as e:
        db.rollback()
        print(f"An unexpected error occurred while saving data for {filename}: {e}")
        return False, None

 