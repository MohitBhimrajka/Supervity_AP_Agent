from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload
from typing import List, Dict, Any, Tuple
from thefuzz import process as fuzzy_process

from app.db import models
from app.config import PRICE_TOLERANCE_PERCENT
from .exceptions import *

# This is the new entry point for the matching engine.
def run_match_for_invoice(db: Session, invoice_db_id: int):
    """
    Performs a comprehensive, INVOICE-centric 3-way match.
    This function is idempotent and can be run multiple times.
    """
    # Load the invoice and ALL its related documents in one efficient query
    invoice = db.query(models.Invoice).options(
        joinedload(models.Invoice.purchase_orders),
        joinedload(models.Invoice.grns).joinedload(models.GoodsReceiptNote.po)
    ).filter(models.Invoice.id == invoice_db_id).first()

    if not invoice:
        print(f"[ERROR] Matching engine called with non-existent invoice database ID: {invoice_db_id}")
        return

    print(f"\n--- Running Matching Engine for Invoice: {invoice.invoice_id} (DB ID: {invoice.id}) ---")

    # Start a fresh trace for this run
    trace: List[Dict[str, Any]] = []
    add_trace(trace, "Initialisation", "INFO", f"Starting validation for Invoice {invoice.invoice_id}.")

    # --- Step 1: Gather all related documents ---
    related_pos = invoice.purchase_orders
    related_grns = invoice.grns

    # Also get POs linked via GRNs
    for grn in related_grns:
        if grn.po and grn.po not in related_pos:
            related_pos.append(grn.po)

    if not related_pos:
        add_trace(trace, "Document Validation", "INFO", "This is a Non-PO Invoice. It requires manual review and GL coding.")
        # Set a specific status or add a flag if needed, but for now, needs_review is fine.
        invoice.status = models.DocumentStatus.needs_review
        _finalize_invoice_status(invoice, trace, db, is_non_po=True) # Pass a flag
        return

    add_trace(trace, "Document Discovery", "INFO", 
              f"Found {len(related_pos)} related PO(s) and {len(related_grns)} related GRN(s).",
              {"po_numbers": [p.po_number for p in related_pos], "grn_numbers": [g.grn_number for g in related_grns]})

    # --- Step 2: Aggregate all PO and GRN line items for easy lookup ---
    po_items_map = {}
    for po in related_pos:
        for item in (po.line_items or []):
            # Key by description for fuzzy matching, but store the PO number
            description = item.get('description', '')
            po_items_map[f"{description} (PO: {po.po_number})"] = {**item, 'po_number': po.po_number}
    
    grn_items_map = {}
    for grn in related_grns:
         for item in (grn.line_items or []):
            description = item.get('description', '')
            grn_items_map[f"{description} (GRN: {grn.grn_number})"] = {**item, 'grn_number': grn.grn_number}

    # --- Step 3: Get Vendor-Specific Tolerance ---
    vendor_setting = db.query(models.VendorSetting).filter_by(vendor_name=invoice.vendor_name).first()
    price_tolerance = vendor_setting.price_tolerance_percent if vendor_setting and vendor_setting.price_tolerance_percent is not None else PRICE_TOLERANCE_PERCENT
    add_trace(trace, "Configuration", "INFO", f"Using price tolerance of {price_tolerance}% for vendor '{invoice.vendor_name}'.")

    # --- Step 4: Duplicate Check ---
    # (This logic remains largely the same)
    potential_duplicates = db.query(models.Invoice).filter(
        models.Invoice.id != invoice.id,
        models.Invoice.vendor_name == invoice.vendor_name,
        models.Invoice.status.in_([models.DocumentStatus.approved_for_payment, models.DocumentStatus.paid]),
        (models.Invoice.invoice_id == invoice.invoice_id) | (models.Invoice.grand_total == invoice.grand_total)
    ).all()
    if potential_duplicates:
        dup_ids = [d.invoice_id for d in potential_duplicates]
        add_trace(trace, "Duplicate Check", "FAIL", f"Potential duplicate of already processed invoices: {', '.join(dup_ids)}", {"matched_duplicates": dup_ids})
    else:
        add_trace(trace, "Duplicate Check", "PASS", "No potential duplicates found.")

    # --- Step 5: Line Item Validation ---
    if not invoice.line_items:
        add_trace(trace, "Line Item Validation", "FAIL", "Invoice contains no line items to validate.")
    else:
        for inv_item in invoice.line_items:
            inv_desc = inv_item.get('description', '')
            inv_qty = inv_item.get('quantity')
            inv_price = inv_item.get('unit_price')
            
            step_prefix = f"Item '{inv_desc}'"

            # Match invoice line to a PO line
            po_item_key, po_item = _find_best_match(inv_desc, po_items_map)
            if not po_item:
                add_trace(trace, f"{step_prefix} - PO Item Match", "FAIL", f"Item not found on any linked POs.")
                continue  # Skip further checks for this item

            po_number_for_item = po_item.get('po_number')
            add_trace(trace, f"{step_prefix} - PO Item Match", "PASS", f"Matched to item on PO {po_number_for_item}.", {"po_item_key": po_item_key})

            # Match invoice line to a GRN line (if GRNs exist)
            grn_qty = None
            if related_grns:
                grn_item_key, grn_item = _find_best_match(inv_desc, grn_items_map)
                if not grn_item:
                    add_trace(trace, f"{step_prefix} - GRN Item Match", "FAIL", f"Item was received, but description '{inv_desc}' doesn't match any GRN line item.", {"invoice_item": inv_desc})
                else:
                    grn_qty = grn_item.get('received_qty')
                    add_trace(trace, f"{step_prefix} - GRN Item Match", "PASS", f"Matched to GRN {grn_item.get('grn_number')}.", {"grn_item_key": grn_item_key})

            # Quantity Match (3-way or 2-way)
            qty_to_compare = grn_qty if grn_qty is not None else po_item.get('ordered_qty')
            source_doc = "GRN" if grn_qty is not None else "PO"
            
            if inv_qty != qty_to_compare:
                add_trace(trace, f"{step_prefix} - Quantity Match", "FAIL", 
                          f"Billed quantity ({inv_qty}) differs from {source_doc} quantity ({qty_to_compare}).", 
                          {"invoice_qty": inv_qty, f"{source_doc.lower()}_qty": qty_to_compare})
            else:
                add_trace(trace, f"{step_prefix} - Quantity Match", "PASS", f"Billed quantity ({inv_qty}) matches {source_doc} quantity.")
            
            # Price Match (always against PO)
            po_price = po_item.get('unit_price')
            if inv_price is not None and po_price is not None:
                tolerance_amount = (price_tolerance / 100) * po_price
                if abs(inv_price - po_price) > tolerance_amount:
                    add_trace(trace, f"{step_prefix} - Price Match", "FAIL", 
                              f"Invoice price (${inv_price:.2f}) is outside tolerance of PO price (${po_price:.2f}).", 
                              {"invoice_price": inv_price, "po_price": po_price, "tolerance_percent": price_tolerance})
                else:
                    add_trace(trace, f"{step_prefix} - Price Match", "PASS", "Invoice price is within tolerance.")

    # --- Step 6: Final Decision ---
    _finalize_invoice_status(invoice, trace, db)


def _finalize_invoice_status(invoice: models.Invoice, trace: List, db: Session, is_non_po: bool = False):
    """Sets the final status of the invoice based on the trace and commits to DB."""
    has_failures = any(t['status'] == 'FAIL' for t in trace)
    invoice.match_trace = trace

    # If it's a non-PO invoice, it always needs review, regardless of other "failures".
    if is_non_po:
        invoice.status = models.DocumentStatus.needs_review
        add_trace(trace, "Final Result", "INFO", "Non-PO invoice queued for GL coding and manual approval.")
        print(f"     [INFO] Non-PO Invoice {invoice.invoice_id} requires review.")
    elif has_failures:
        invoice.status = models.DocumentStatus.needs_review
        add_trace(trace, "Final Result", "FAIL", "Invoice requires manual review due to one or more validation failures.")
        print(f"     [FAIL] Invoice {invoice.invoice_id} requires review.")
    else:
        invoice.status = models.DocumentStatus.approved_for_payment
        add_trace(trace, "Final Result", "PASS", "All checks passed. Invoice is approved for payment.")
        print(f"     [SUCCESS] Invoice {invoice.invoice_id} approved for payment.")
    
    db.commit()
    print(f"--- Matching Engine finished for Invoice: {invoice.invoice_id} ---")


def add_trace(trace_list: List, step: str, status: str, message: str, details: Dict = None):
    """Standardizes adding entries to the match trace."""
    trace_list.append({
        "step": step,
        "status": status,  # 'PASS', 'FAIL', 'INFO'
        "message": message,
        "details": details or {}
    })

def _find_best_match(query: str, choices_map: Dict[str, Any], score_cutoff=85) -> Tuple[str | None, Any | None]:
    """Finds the best fuzzy match for a query string in a dictionary of choices."""
    if not query or not choices_map:
        return None, None
    # The `process.extractOne` is a powerful tool from thefuzz library
    best_match = fuzzy_process.extractOne(query, choices_map.keys(), score_cutoff=score_cutoff)
    if best_match:
        # best_match is a tuple: (matched_key, score)
        return best_match[0], choices_map[best_match[0]]
    return None, None

# NOTE: The _check_cumulative_billing function is removed for now. It adds significant complexity
# to the many-to-many logic and can be reintroduced as a separate, advanced feature later.
# The current line-item-level matching is the highest priority. 