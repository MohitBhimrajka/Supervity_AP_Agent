# src/app/modules/matching/comparison.py
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from typing import List, Dict, Any, Tuple
from thefuzz import process as fuzzy_process
import math

from app.db import models
from app.db import schemas

def _find_best_match(query: str, choices_map: Dict[str, Any], score_cutoff=63) -> Tuple[str | None, Any | None]:
    """Finds the best fuzzy match for a query string in a dictionary of choices."""
    if not query or not choices_map:
        return None, None
    best_match = fuzzy_process.extractOne(query, list(choices_map.keys()), score_cutoff=score_cutoff)
    if best_match:
        return best_match[0], choices_map[best_match[0]]
    return None, None

def prepare_comparison_data(db: Session, invoice_db_id: int) -> Dict[str, Any]:
    """
    Prepares a detailed, line-by-line comparison between an invoice,
    and all its related POs and GRNs, and includes proactive suggestions.
    """
    invoice = db.query(models.Invoice).options(
        joinedload(models.Invoice.purchase_orders),
        joinedload(models.Invoice.grns)
    ).filter(models.Invoice.id == invoice_db_id).first()

    if not invoice:
        return {"error": "Invoice not found"}

    # Aggregate all related PO and GRN line items for easy lookup
    po_items_map: Dict[str, Dict] = {}
    for po in invoice.purchase_orders:
        for item in (po.line_items or []):
            description = item.get('description', '')
            if not description: continue
            key = f"{description}##{po.po_number}"
            po_items_map[key] = {**item, 'po_number': po.po_number, 'po_db_id': po.id}
    
    grn_items_map: Dict[str, Dict] = {}
    for grn in invoice.grns:
        for item in (grn.line_items or []):
            description = item.get('description', '')
            if not description: continue
            key = f"{description}##{grn.grn_number}"
            grn_items_map[key] = {**item, 'grn_number': grn.grn_number}

    comparison_lines = []
    for inv_item in (invoice.line_items or []):
        inv_desc = inv_item.get('description', '')
        po_key_match, po_item_match = _find_best_match(inv_desc, po_items_map)
        grn_key_match, grn_item_match = _find_best_match(inv_desc, grn_items_map)

        comparison_lines.append({
            "invoice_line": inv_item,
            "po_line": po_item_match,
            "grn_line": grn_item_match,
            "po_number": po_item_match.get('po_number') if po_item_match else inv_item.get('po_number'),
            "grn_number": grn_item_match.get('grn_number') if grn_item_match else None
        })

    # Prepare header-level data for all linked documents with explicit total extraction.
    related_pos_data = []
    for po in invoice.purchase_orders:
        # Explicitly get the grand total from the raw payload
        grand_total = (po.raw_data_payload or {}).get('po_grand_total')
        related_pos_data.append({
            'id': po.id,
            'po_number': po.po_number,
            'order_date': str(po.order_date) if po.order_date else None,
            'line_items': po.line_items,
            'po_grand_total': grand_total
        })

    invoice_doc = {"file_path": invoice.file_path}
    po_doc = {"file_path": invoice.purchase_orders[0].file_path} if invoice.purchase_orders else None
    grn_doc = {"file_path": invoice.grns[0].file_path} if invoice.grns else None

    # Suggestion Logic (remains the same)
    suggestion = None
    if invoice.status == models.DocumentStatus.needs_review and invoice.match_trace:
        first_failure = next((step for step in invoice.match_trace if step.get("status") == "FAIL"), None)
        if first_failure:
            failure_step_name = first_failure.get("step", "")
            exception_type = ""
            if "Price Match" in failure_step_name: exception_type = "PriceMismatchException"
            elif "Quantity Match" in failure_step_name: exception_type = "QuantityMismatchException"
            if exception_type:
                heuristic = db.query(models.LearnedHeuristic).filter(
                    models.LearnedHeuristic.vendor_name == invoice.vendor_name,
                    models.LearnedHeuristic.exception_type == exception_type,
                    models.LearnedHeuristic.confidence_score >= 0.8,
                    models.LearnedHeuristic.resolution_action == 'matched'
                ).order_by(models.LearnedHeuristic.confidence_score.desc()).first()
                if heuristic:
                    condition_text = ""
                    if exception_type == "PriceMismatchException":
                        max_variance = heuristic.learned_condition.get("max_variance_percent", 0)
                        condition_text = f"price mismatches of up to {max_variance}%"
                    suggestion = { "message": f"You have previously approved {condition_text} for {invoice.vendor_name}. This invoice appears to match that pattern.", "action": heuristic.resolution_action, "confidence": heuristic.confidence_score }

    return {
        "invoice_id": invoice.invoice_id,
        "vendor_name": invoice.vendor_name,
        "grand_total": invoice.grand_total,
        "line_item_comparisons": comparison_lines,
        "related_pos": related_pos_data,
        "related_grns": [schemas.GoodsReceiptNote.from_orm(grn).model_dump(mode='json') for grn in invoice.grns],
        "invoice_notes": invoice.notes,
        "invoice_status": invoice.status.value,
        "match_trace": invoice.match_trace or [],
        "gl_code": invoice.gl_code,
        "related_documents": { "invoice": invoice_doc, "po": po_doc, "grn": grn_doc },
        "all_related_documents": {
            "pos": [{"file_path": po.file_path, "po_number": po.po_number} for po in invoice.purchase_orders],
            "grns": [{"file_path": grn.file_path, "grn_number": grn.grn_number} for grn in invoice.grns]
        },
        "suggestion": suggestion,
    } 