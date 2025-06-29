# src/app/modules/matching/comparison.py
from sqlalchemy.orm import Session, joinedload
from typing import List, Dict, Any, Tuple
from thefuzz import process as fuzzy_process

from app.db import models

def _find_best_match(query: str, choices_map: Dict[str, Any], score_cutoff=85) -> Tuple[str | None, Any | None]:
    """Finds the best fuzzy match for a query string in a dictionary of choices."""
    if not query or not choices_map:
        return None, None
    best_match = fuzzy_process.extractOne(query, choices_map.keys(), score_cutoff=score_cutoff)
    if best_match:
        return best_match[0], choices_map[best_match[0]]
    return None, None

def prepare_comparison_data(db: Session, invoice_db_id: int) -> Dict[str, Any]:
    """
    Prepares a detailed, line-by-line comparison between an invoice,
    and all its related POs and GRNs.
    """
    invoice = db.query(models.Invoice).options(
        joinedload(models.Invoice.purchase_orders),
        joinedload(models.Invoice.grns)
    ).filter(models.Invoice.id == invoice_db_id).first()

    if not invoice:
        return {"error": "Invoice not found"}

    # Aggregate all related PO and GRN line items
    po_items_map = {}
    for po in invoice.purchase_orders:
        for item in (po.line_items or []):
            description = item.get('description', '')
            # Add PO number to description to make keys unique
            po_items_map[f"{description}##{po.po_number}"] = {**item, 'po_number': po.po_number}
    
    grn_items_map = {}
    for grn in invoice.grns:
        for item in (grn.line_items or []):
            description = item.get('description', '')
            # Add GRN number to description to make keys unique
            grn_items_map[f"{description}##{grn.grn_number}"] = {**item, 'grn_number': grn.grn_number}

    comparison_lines = []
    # Use invoice line items as the basis for comparison
    for inv_item in (invoice.line_items or []):
        inv_desc = inv_item.get('description', '')
        
        # Find the best matching PO item
        po_key_match, po_item_match = _find_best_match(inv_desc, po_items_map)
        
        # Find the best matching GRN item
        grn_key_match, grn_item_match = _find_best_match(inv_desc, grn_items_map)

        comparison_lines.append({
            "invoice_line": inv_item,
            "po_line": po_item_match,
            "grn_line": grn_item_match,
            "po_number": po_item_match.get('po_number') if po_item_match else inv_item.get('po_number'),
            "grn_number": grn_item_match.get('grn_number') if grn_item_match else None
        })

    # Also prepare header-level data for all linked documents
    related_pos_data = [
        {**(po.raw_data_payload or {}), 'po_number': po.po_number, 'id': po.id} 
        for po in invoice.purchase_orders
    ]
    related_grns_data = [
        {
            "grn_number": grn.grn_number,
            "po_number": grn.po_number,
            "received_date": str(grn.received_date),
            "line_items": grn.line_items
        }
        for grn in invoice.grns
    ]
    
    # Construct the document info needed by the frontend DocumentViewer.
    # It shows one PO/GRN at a time, so we'll provide the first linked document.
    invoice_doc = {"file_path": invoice.file_path}
    po_doc = {"file_path": invoice.purchase_orders[0].file_path} if invoice.purchase_orders else None
    grn_doc = {"file_path": invoice.grns[0].file_path} if invoice.grns else None

    return {
        "line_item_comparisons": comparison_lines,
        "related_pos": related_pos_data,
        "related_grns": related_grns_data,
        "invoice_notes": invoice.notes,
        "invoice_status": invoice.status.value,
        # Add the missing fields:
        "match_trace": invoice.match_trace or [],  # Ensure it's a list, not None
        "gl_code": invoice.gl_code,
        "related_documents": {
            "invoice": invoice_doc,
            "po": po_doc,
            "grn": grn_doc,
        }
    } 