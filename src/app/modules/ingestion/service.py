# src/app/modules/ingestion/service.py
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Dict, Tuple, List, Any
from datetime import datetime, date

from app.db import models
from app.modules.ingestion import extractor
from app.utils import unit_converter

def convert_string_to_date(date_string: str | None) -> date | None:
    """
    Converts a string date in YYYY-MM-DD format to a Python date object.
    Returns None if the input is None or invalid.
    """
    if not date_string:
        return None
    
    try:
        return datetime.strptime(date_string, "%Y-%m-%d").date()
    except (ValueError, TypeError) as e:
        print(f"Warning: Could not parse date '{date_string}': {e}")
        return None

def validate_required_fields(extracted_data: Dict, doc_type: str) -> Tuple[bool, str]:
    """
    Validates that required fields are present for each document type.
    Returns (is_valid, error_message).
    """
    if doc_type == "Purchase Order":
        if not extracted_data.get("po_number"):
            return False, "Purchase Order is missing required field: po_number"
    
    elif doc_type == "Goods Receipt Note":
        if not extracted_data.get("grn_number"):
            return False, "Goods Receipt Note is missing required field: grn_number"
        if not extracted_data.get("po_number"):
            return False, "Goods Receipt Note is missing required field: po_number"
    
    elif doc_type == "Invoice":
        if not extracted_data.get("invoice_id"):
            return False, "Invoice is missing required field: invoice_id"
    
    return True, ""

def prepare_po_data(extracted_data: Dict) -> Dict:
    """Prepare purchase order data with proper date conversion."""
    return {
        'po_number': extracted_data.get("po_number"),
        'vendor_name': extracted_data.get("vendor_name"),
        'buyer_name': extracted_data.get("buyer_name"),
        'order_date': convert_string_to_date(extracted_data.get("order_date")),
        'line_items': extracted_data.get("line_items"),
        'raw_data_payload': extracted_data,
    }

def prepare_grn_data(extracted_data: Dict) -> Dict:
    """Prepare GRN data with proper date conversion."""
    return {
        'grn_number': extracted_data.get("grn_number"),
        'po_number': extracted_data.get("po_number"),
        'received_date': convert_string_to_date(extracted_data.get("received_date")),
        'line_items': extracted_data.get("line_items"),
    }

def prepare_invoice_data(extracted_data: Dict, job_id: int) -> Dict:
    """Prepare invoice data with proper date conversion and initial status."""
    return {
        'invoice_id': extracted_data.get("invoice_id"),
        'vendor_name': extracted_data.get("vendor_name"),
        'buyer_name': extracted_data.get("buyer_name"),
        'invoice_date': convert_string_to_date(extracted_data.get("invoice_date")),
        'due_date': convert_string_to_date(extracted_data.get("due_date")),
        'subtotal': extracted_data.get("subtotal"),
        'tax': extracted_data.get("tax"),
        'grand_total': extracted_data.get("grand_total"),
        'line_items': extracted_data.get("line_items"),
        'discount_terms': extracted_data.get("discount_terms"),
        'discount_amount': extracted_data.get("discount_amount"),
        'discount_due_date': convert_string_to_date(extracted_data.get("discount_due_date")),
        'related_po_numbers': extracted_data.get("related_po_numbers", []),
        'job_id': job_id,
        'status': models.DocumentStatus.ingested,
    }

def ingest_document(db: Session, job_id: int, file_content: bytes, filename: str) -> Tuple[bool, List[str] | None, Dict[str, Any]]:
    """
    Orchestrates the ingestion of a single document.
    1. Extracts data using the extractor.
    2. Normalizes line item units.
    3. Saves the data and links documents.
    """
    print(f"--- Ingesting file: {filename} for Job ID: {job_id} ---")

    extracted_data = extractor.extract_data_from_pdf(file_content)
    if not extracted_data:
        msg = f"Data extraction failed for {filename}. The document may be unreadable or not a valid format."
        print(msg)
        return False, None, {"error": msg}

    doc_type = extracted_data.get("document_type")
    if not doc_type:
        msg = f"Could not determine document type for {filename}."
        print(msg)
        return False, None, {"error": msg}
        
    if 'line_items' in extracted_data and extracted_data['line_items']:
        normalized_items = []
        for item in extracted_data['line_items']:
            normalized_items.append(unit_converter.normalize_item(item))
        extracted_data['line_items'] = normalized_items
        print(f"    -> Normalized {len(normalized_items)} line item(s) for {filename}.")

    is_valid, error_message = validate_required_fields(extracted_data, doc_type)
    if not is_valid:
        print(f"Validation failed for {filename}: {error_message}. Skipping.")
        return False, None, {"error": error_message}

    affected_po_numbers: set[str] = set()

    try:
        if doc_type == "Purchase Order":
            po_number = extracted_data.get("po_number")
            existing_po = db.query(models.PurchaseOrder).filter_by(po_number=po_number).first()
            if existing_po:
                print(f"Purchase Order {po_number} already exists. Skipping creation.")
            else:
                po_data = prepare_po_data(extracted_data)
                po_data['file_path'] = filename
                db_po = models.PurchaseOrder(**po_data)
                db.add(db_po)
            affected_po_numbers.add(po_number)

        elif doc_type == "Goods Receipt Note":
            grn_number = extracted_data.get("grn_number")
            po_number = extracted_data.get("po_number")
            existing_grn = db.query(models.GoodsReceiptNote).filter_by(grn_number=grn_number).first()
            if existing_grn:
                print(f"GRN {grn_number} already exists. Skipping creation.")
            else:
                po = db.query(models.PurchaseOrder).filter_by(po_number=po_number).first()
                if not po:
                    print(f"Warning: GRN {grn_number} references non-existent PO {po_number}. GRN will be saved but cannot be linked.")
                
                grn_data = prepare_grn_data(extracted_data)
                grn_data['file_path'] = filename
                grn_data['po'] = po
                db_grn = models.GoodsReceiptNote(**grn_data)
                db.add(db_grn)
            affected_po_numbers.add(po_number)
            
        elif doc_type == "Invoice":
            invoice_id = extracted_data.get("invoice_id")
            existing_invoice = db.query(models.Invoice).filter_by(invoice_id=invoice_id).first()
            if existing_invoice:
                 print(f"Invoice {invoice_id} already exists. Skipping creation.")
            else:
                invoice_data = prepare_invoice_data(extracted_data, job_id)
                invoice_data['file_path'] = filename
                db_invoice = models.Invoice(**invoice_data)

                po_numbers_to_link = extracted_data.get("related_po_numbers", [])
                grn_numbers_to_link = extracted_data.get("related_grn_numbers", [])

                if po_numbers_to_link:
                    pos = db.query(models.PurchaseOrder).filter(models.PurchaseOrder.po_number.in_(po_numbers_to_link)).all()
                    db_invoice.purchase_orders.extend(pos)
                    for po in pos:
                        affected_po_numbers.add(po.po_number)

                if grn_numbers_to_link:
                    grns = db.query(models.GoodsReceiptNote).filter(models.GoodsReceiptNote.grn_number.in_(grn_numbers_to_link)).all()
                    db_invoice.grns.extend(grns)
                    for grn in grns:
                        if grn.po_number:
                            affected_po_numbers.add(grn.po_number)

                db.add(db_invoice)
        else:
            msg = f"Unknown document type '{doc_type}' for {filename}."
            print(msg)
            return False, None, {"error": msg}

        db.commit()
        print(f"Successfully processed and saved {doc_type} from {filename} to database.")
        return True, list(affected_po_numbers), extracted_data

    except IntegrityError as e:
        db.rollback()
        msg = f"Database integrity error for {filename}. A document with this ID likely already exists."
        print(f"{msg}: {e}")
        return False, None, {"error": msg, **extracted_data}
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        msg = f"An unexpected error occurred while saving data for {filename}: {e}"
        print(msg)
        return False, None, {"error": msg, **extracted_data}

 