from sqlalchemy.orm import Session, joinedload
from typing import List, Dict, Any, Tuple
from thefuzz import process as fuzzy_process
import math

from app.db import models
from app.config import PRICE_TOLERANCE_PERCENT
from .exceptions import *

# This is the new entry point for the matching engine.
def run_match_for_invoice(db: Session, invoice_db_id: int):
    """
    Performs a comprehensive, INVOICE-centric 3-way match using normalized data.
    This function is idempotent and can be run multiple times.
    """
    invoice = db.query(models.Invoice).options(
        joinedload(models.Invoice.purchase_orders),
        joinedload(models.Invoice.grns).joinedload(models.GoodsReceiptNote.po)
    ).filter(models.Invoice.id == invoice_db_id).first()

    if not invoice:
        print(f"[ERROR] Matching engine called with non-existent invoice DB ID: {invoice_db_id}")
        return

    print(f"\n--- Running Matching Engine for Invoice: {invoice.invoice_id} (DB ID: {invoice.id}) ---")

    trace: List[Dict[str, Any]] = []
    add_trace(trace, "Initialisation", "INFO", f"Starting validation for Invoice {invoice.invoice_id}.")

    # --- Step 1: Gather all related documents ---
    related_pos = invoice.purchase_orders
    related_grns = invoice.grns
    for grn in related_grns:
        if grn.po and grn.po not in related_pos:
            related_pos.append(grn.po)

    if not related_pos:
        add_trace(trace, "Document Validation", "INFO", "This is a Non-PO Invoice. Requires manual review.")
        _finalize_invoice_status(invoice, trace, db, is_non_po=True)
        return

    add_trace(trace, "Document Discovery", "INFO",
              f"Found {len(related_pos)} PO(s) and {len(related_grns)} GRN(s).",
              {"po_numbers": [p.po_number for p in related_pos], "grn_numbers": [g.grn_number for g in related_grns]})
    
    # --- Step 2: Aggregate all PO and GRN line items for easy lookup ---
    po_items_map = {f"{item.get('description', '')}##{po.po_number}": {**item, 'po_number': po.po_number, 'order_date': po.order_date} for po in related_pos for item in (po.line_items or [])}
    grn_items_map = {f"{item.get('description', '')}##{grn.grn_number}": {**item, 'grn_number': grn.grn_number} for grn in related_grns for item in (grn.line_items or [])}

    # --- Step 3: Get Vendor-Specific Tolerance ---
    vendor_setting = db.query(models.VendorSetting).filter_by(vendor_name=invoice.vendor_name).first()
    price_tolerance = vendor_setting.price_tolerance_percent if vendor_setting and vendor_setting.price_tolerance_percent is not None else PRICE_TOLERANCE_PERCENT
    add_trace(trace, "Configuration", "INFO", f"Using price tolerance of {price_tolerance}% for '{invoice.vendor_name}'.")

    # --- Step 4: Duplicate Check ---
    # This remains an important check
    potential_duplicates = db.query(models.Invoice).filter(
        models.Invoice.id != invoice.id,
        models.Invoice.vendor_name == invoice.vendor_name,
        models.Invoice.invoice_id == invoice.invoice_id,
        models.Invoice.status.in_([models.DocumentStatus.approved_for_payment, models.DocumentStatus.paid])
    ).all()
    if potential_duplicates:
        dup_ids = [d.invoice_id for d in potential_duplicates]
        add_trace(trace, "Duplicate Check", "FAIL", f"Potential duplicate of already processed invoices: {', '.join(dup_ids)}", {"matched_duplicates": dup_ids})
    else:
        add_trace(trace, "Duplicate Check", "PASS", "No potential duplicates found.")

    # --- Step 5: Line Item Validation Loop ---
    if not invoice.line_items:
        add_trace(trace, "Line Item Validation", "FAIL", "Invoice contains no line items to validate.")
    else:
        for inv_item in invoice.line_items:
            inv_desc = inv_item.get('description', '')
            step_prefix = f"Item '{inv_desc}'"
            
            # Match to PO item
            po_key, po_item = _find_best_match(inv_desc, po_items_map)
            if not po_item:
                add_trace(trace, f"{step_prefix} - PO Item Match", "FAIL", "Item not found on any linked POs.")
                continue
            
            add_trace(trace, f"{step_prefix} - PO Item Match", "PASS", f"Matched to item on PO {po_item.get('po_number')}.")

            # --- NEW: TIMING CHECK ---
            if invoice.invoice_date and po_item.get('order_date') and invoice.invoice_date < po_item['order_date']:
                 add_trace(trace, f"{step_prefix} - Timing Check", "FAIL", 
                           f"Invoice date ({invoice.invoice_date}) is before PO date ({po_item['order_date']}).",
                           {"invoice_date": str(invoice.invoice_date), "po_date": str(po_item['order_date'])})
            else:
                 add_trace(trace, f"{step_prefix} - Timing Check", "PASS", "Invoice date is after PO date.")
            
            # Match to GRN item
            grn_item = None
            if related_grns:
                grn_key, grn_item = _find_best_match(inv_desc, grn_items_map)

            # --- NORMALIZED QUANTITY MATCH ---
            inv_norm_qty = inv_item.get('normalized_qty')
            
            # Compare to GRN first, fallback to PO
            if grn_item and grn_item.get('normalized_qty') is not None:
                comp_norm_qty = grn_item.get('normalized_qty')
                source_doc = "GRN"
                details = {"invoice_qty": inv_item.get('quantity'), "invoice_unit": inv_item.get('unit'), "grn_qty": grn_item.get('received_qty'), "grn_unit": grn_item.get('unit')}
            else:
                comp_norm_qty = po_item.get('normalized_qty')
                source_doc = "PO"
                details = {"invoice_qty": inv_item.get('quantity'), "invoice_unit": inv_item.get('unit'), "po_qty": po_item.get('ordered_qty'), "po_unit": po_item.get('unit')}

            if inv_norm_qty is not None and comp_norm_qty is not None and not math.isclose(inv_norm_qty, comp_norm_qty, rel_tol=1e-5):
                add_trace(trace, f"{step_prefix} - Quantity Match", "FAIL", f"Normalized quantity ({inv_norm_qty:.2f}) differs from {source_doc} ({comp_norm_qty:.2f}).", details)
            else:
                add_trace(trace, f"{step_prefix} - Quantity Match", "PASS", f"Normalized quantity matches {source_doc}.")

            # --- NORMALIZED PRICE MATCH ---
            inv_norm_price = inv_item.get('normalized_unit_price')
            po_norm_price = po_item.get('normalized_unit_price')
            
            if inv_norm_price is not None and po_norm_price is not None:
                tolerance_amount = (price_tolerance / 100) * po_norm_price
                if abs(inv_norm_price - po_norm_price) > tolerance_amount:
                    add_trace(trace, f"{step_prefix} - Price Match", "FAIL", 
                              f"Normalized invoice price (${inv_norm_price:.4f}) is outside tolerance of PO price (${po_norm_price:.4f}).",
                              {"inv_price": inv_item.get('unit_price'), "inv_unit": inv_item.get('unit'), "po_price": po_item.get('unit_price'), "po_unit": po_item.get('unit'), "tolerance_percent": price_tolerance})
                else:
                    add_trace(trace, f"{step_prefix} - Price Match", "PASS", "Normalized price is within tolerance.")
    
    # --- Step 6: Financial Sanity Check ---
    if invoice.line_items and invoice.subtotal is not None and invoice.grand_total is not None:
        calculated_subtotal = sum(item.get('line_total', 0) for item in invoice.line_items)
        if not math.isclose(calculated_subtotal, invoice.subtotal, rel_tol=0.01): # 1% tolerance for rounding
            add_trace(trace, "Financials - Subtotal Check", "FAIL", 
                      f"Sum of line items (${calculated_subtotal:.2f}) does not match invoice subtotal (${invoice.subtotal:.2f}).",
                      {"calculated_subtotal": calculated_subtotal, "invoice_subtotal": invoice.subtotal})
        else:
             add_trace(trace, "Financials - Subtotal Check", "PASS", "Sum of line items matches invoice subtotal.")
             
        # Only check grand total if subtotal matches, to avoid cascading errors
        if invoice.tax is not None:
            calculated_grand_total = invoice.subtotal + invoice.tax
            if not math.isclose(calculated_grand_total, invoice.grand_total, rel_tol=0.01):
                add_trace(trace, "Financials - Grand Total Check", "FAIL",
                          f"Subtotal + Tax (${calculated_grand_total:.2f}) does not match invoice grand total (${invoice.grand_total:.2f}).",
                          {"calculated_grand_total": calculated_grand_total, "invoice_grand_total": invoice.grand_total})
            else:
                add_trace(trace, "Financials - Grand Total Check", "PASS", "Subtotal + Tax matches invoice grand total.")


    # --- Step 7: Final Decision ---
    _finalize_invoice_status(invoice, trace, db)

def _finalize_invoice_status(invoice: models.Invoice, trace: List, db: Session, is_non_po: bool = False):
    """Sets the final status of the invoice based on the trace and commits to DB."""
    has_failures = any(t['status'] == 'FAIL' for t in trace)
    invoice.match_trace = trace
    
    category = None
    if has_failures or is_non_po:
        # Determine the primary reason for failure
        if is_non_po:
            category = "missing_document"
        else:
            category = "data_mismatch" # Default
            for step in trace:
                if step.get("status") == "FAIL":
                    if "Timing Check" in step.get("step", "") or "Duplicate Check" in step.get("step", ""):
                        category = "policy_violation"
                        break
                    if "Item not found" in step.get("message", ""):
                        category = "missing_document"
                        break
    
    invoice.review_category = category

    if is_non_po:
        invoice.status = models.DocumentStatus.needs_review
        add_trace(trace, "Final Result", "INFO", "Non-PO invoice queued for GL coding and manual approval.")
        print(f"     [INFO] Non-PO Invoice {invoice.invoice_id} requires review. Category: {category}")
    elif has_failures:
        invoice.status = models.DocumentStatus.needs_review
        add_trace(trace, "Final Result", "FAIL", "Invoice requires manual review due to validation failures.")
        print(f"     [FAIL] Invoice {invoice.invoice_id} requires review. Category: {category}")
    else:
        invoice.status = models.DocumentStatus.approved_for_payment
        invoice.review_category = None
        add_trace(trace, "Final Result", "PASS", "All checks passed. Invoice approved for payment.")
        print(f"     [SUCCESS] Invoice {invoice.invoice_id} approved for payment.")
    
    db.commit()
    print(f"--- Matching Engine finished for Invoice: {invoice.invoice_id} ---")

def add_trace(trace_list: List, step: str, status: str, message: str, details: Dict = None):
    """Standardizes adding entries to the match trace."""
    trace_list.append({
        "step": step,
        "status": status,
        "message": message,
        "details": details or {}
    })

def _find_best_match(query: str, choices_map: Dict[str, Any], score_cutoff=85) -> Tuple[str | None, Any | None]:
    """Finds the best fuzzy match for a query string in a dictionary of choices."""
    if not query or not choices_map:
        return None, None
    best_match = fuzzy_process.extractOne(query, choices_map.keys(), score_cutoff=score_cutoff)
    if best_match:
        return best_match[0], choices_map[best_match[0]]
    return None, None

# NOTE: The _check_cumulative_billing function is removed for now. It adds significant complexity
# to the many-to-many logic and can be reintroduced as a separate, advanced feature later.
# The current line-item-level matching is the highest priority. 