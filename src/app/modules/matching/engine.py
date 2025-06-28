from sqlalchemy.orm import Session
from typing import List, Dict, Any, Tuple
from thefuzz import process as fuzzy_process

from app.db import models
from app.config import PRICE_TOLERANCE_PERCENT
from .exceptions import *

# --- NEW HELPER FOR TRACING ---
def add_trace(trace_list: List, step: str, status: str, message: str, details: Dict = None):
    """Standardizes adding entries to the match trace."""
    trace_list.append({
        "step": step,
        "status": status, # 'PASS', 'FAIL', 'INFO'
        "message": message,
        "details": details or {}
    })

def run_match_for_po(db: Session, po_number: str):
    """
    Performs a comprehensive, PO-centric 3-way match using a detailed trace.
    This function is idempotent and can be run multiple times.
    """
    print(f"\n--- Running Matching Engine for PO: {po_number} ---")
    po = db.query(models.PurchaseOrder).filter_by(po_number=po_number).first()
    
    # --- REFACTORED LOGIC ---
    
    # Find all invoices related to this PO
    invoices_to_process = db.query(models.Invoice).join(models.GoodsReceiptNote, isouter=True).filter(
        (models.GoodsReceiptNote.po_number == po_number) |
        (models.Invoice.po_number == po_number)
    ).distinct().all()

    if not po:
        # Handle invoices that reference a non-existent PO
        for inv in invoices_to_process:
            inv.status = models.DocumentStatus.needs_review
            inv.match_trace = [] # Clear previous trace
            add_trace(inv.match_trace, "Document Validation", "FAIL", f"Invoice references PO {po_number}, which does not exist in the system.")
        db.commit()
        print(f"  [ERROR] PO {po_number} not found. Flagged {len(invoices_to_process)} invoices.")
        return

    # Get vendor tolerance
    vendor_setting = db.query(models.VendorSetting).filter_by(vendor_name=po.vendor_name).first()
    price_tolerance = vendor_setting.price_tolerance_percent if vendor_setting and vendor_setting.price_tolerance_percent is not None else PRICE_TOLERANCE_PERCENT

    po_items_map = {item.get('description', ''): item for item in (po.line_items or [])}

    for invoice in invoices_to_process:
        if invoice.status not in [models.DocumentStatus.pending_match, models.DocumentStatus.needs_review]:
            print(f"  -> Skipping Invoice {invoice.invoice_id} (status: {invoice.status.value})")
            continue

        trace: List[Dict[str, Any]] = []
        print(f"  -> Validating Invoice: {invoice.invoice_id}")
        add_trace(trace, "Initialisation", "INFO", f"Starting validation for Invoice {invoice.invoice_id}.")
        add_trace(trace, "Configuration", "INFO", f"Using price tolerance of {price_tolerance}% for vendor '{po.vendor_name}'.")

        # 1. Duplicate Check
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

        # 2. Timing Checks (if GRN exists)
        if invoice.grn:
            if invoice.invoice_date and invoice.grn.received_date and invoice.invoice_date < invoice.grn.received_date:
                add_trace(trace, "Timing Check", "FAIL", f"Invoice Date ({invoice.invoice_date}) is before Goods Receipt Date ({invoice.grn.received_date}).")
            else:
                add_trace(trace, "Timing Check", "PASS", "Invoice date is valid relative to GRN date.")
        else:
            add_trace(trace, "Document Validation", "INFO", "No GRN linked. Performing a 2-way match (Invoice vs. PO).")
        
        # 3. Line Item Validation
        if not invoice.line_items:
            add_trace(trace, "Line Item Validation", "FAIL", "Invoice contains no line items to validate.")
        else:
            for inv_item in invoice.line_items:
                inv_desc = inv_item.get('description', '')
                inv_qty = inv_item.get('quantity')
                inv_price = inv_item.get('unit_price')
                
                step_prefix = f"Item '{inv_desc}'"

                # Item Match
                po_item_desc, po_item = _find_best_match(inv_desc, po_items_map)
                if not po_item:
                    add_trace(trace, f"{step_prefix} - Item Match", "FAIL", f"Item not found on PO {po.po_number}.")
                    continue # Skip further checks for this item

                add_trace(trace, f"{step_prefix} - Item Match", "PASS", f"Matched to PO item '{po_item_desc}'.")

                # Quantity & Price Match (logic branches for 3-way vs 2-way)
                if invoice.grn: # 3-Way Match
                    grn_items_map = {i.get('description',''): i for i in (invoice.grn.line_items or [])}
                    grn_item_desc, grn_item = _find_best_match(inv_desc, grn_items_map)
                    
                    if not grn_item:
                        add_trace(trace, f"{step_prefix} - GRN Item Match", "FAIL", f"Item not found on GRN {invoice.grn.grn_number}.")
                    else:
                        grn_qty = grn_item.get('received_qty')
                        if inv_qty != grn_qty:
                            add_trace(trace, f"{step_prefix} - Quantity Match", "FAIL", f"Billed quantity ({inv_qty}) differs from received quantity ({grn_qty}).", {"invoice_qty": inv_qty, "grn_qty": grn_qty})
                        else:
                            add_trace(trace, f"{step_prefix} - Quantity Match", "PASS", f"Billed quantity ({inv_qty}) matches received quantity.")
                else: # 2-Way Match
                    po_qty = po_item.get('ordered_qty')
                    if inv_qty != po_qty:
                         add_trace(trace, f"{step_prefix} - Quantity Match", "FAIL", f"Billed quantity ({inv_qty}) differs from ordered quantity ({po_qty}).", {"invoice_qty": inv_qty, "po_qty": po_qty})
                    else:
                        add_trace(trace, f"{step_prefix} - Quantity Match", "PASS", "Billed quantity matches ordered quantity.")
                
                # Price Match (always against PO)
                po_price = po_item.get('unit_price')
                if inv_price is not None and po_price is not None:
                    tolerance_amount = (price_tolerance / 100) * po_price
                    if abs(inv_price - po_price) > tolerance_amount:
                        add_trace(trace, f"{step_prefix} - Price Match", "FAIL", f"Invoice price (${inv_price:.2f}) is outside tolerance of PO price (${po_price:.2f}).", {"invoice_price": inv_price, "po_price": po_price, "tolerance_percent": price_tolerance})
                    else:
                        add_trace(trace, f"{step_prefix} - Price Match", "PASS", "Invoice price is within tolerance.")

        # Handle cumulative billing check
        try:
            _check_cumulative_billing(po, po_items_map, db)
            add_trace(trace, "Cumulative Billing Check", "PASS", "No overbilling detected across all invoices for this PO.")
        except OverBillingException as e:
            add_trace(trace, "Cumulative Billing Check", "FAIL", str(e), e.details if hasattr(e, 'details') else {})

        # Final Decision
        has_failures = any(t['status'] == 'FAIL' for t in trace)
        invoice.match_trace = trace # Save the full trace
        
        if has_failures:
            invoice.status = models.DocumentStatus.needs_review
            add_trace(trace, "Final Result", "FAIL", "Invoice requires manual review due to one or more validation failures.")
            print(f"     [FAIL] Invoice {invoice.invoice_id} requires review.")
        else:
            invoice.status = models.DocumentStatus.approved_for_payment
            add_trace(trace, "Final Result", "PASS", "All checks passed. Invoice is approved for payment.")
            print(f"     [SUCCESS] Invoice {invoice.invoice_id} approved for payment.")

    db.commit()
    print(f"--- Matching Engine finished for PO: {po_number} ---")


def _find_best_match(query: str, choices_map: Dict[str, Any], score_cutoff=85) -> Tuple[str | None, Any | None]:
    """Finds the best fuzzy match for a query string in a dictionary of choices."""
    if not query or not choices_map:
        return None, None
    best_match = fuzzy_process.extractOne(query, choices_map.keys(), score_cutoff=score_cutoff)
    if best_match:
        return best_match[0], choices_map[best_match[0]]
    return None, None

def _check_cumulative_billing(po: models.PurchaseOrder, po_items_map: Dict[str, Any], db: Session):
    """
    Checks if the total quantity billed across all invoices for a PO item exceeds the ordered quantity.
    """
    all_related_invoices = db.query(models.Invoice).filter(
        (models.Invoice.po_number == po.po_number) |
        (models.Invoice.grn.has(po_number=po.po_number))
    ).all()

    for po_desc, po_item in po_items_map.items():
        po_ordered_qty = po_item.get('ordered_qty')
        if po_ordered_qty is None: continue
            
        total_billed_qty = 0
        for inv in all_related_invoices:
            if not inv.line_items: continue
            if inv.status not in [models.DocumentStatus.approved_for_payment, models.DocumentStatus.paid]: continue
            
            inv_item_desc, inv_item = _find_best_match(po_desc, {i.get('description', ''): i for i in inv.line_items})
            if inv_item:
                total_billed_qty += inv_item.get('quantity', 0)
        
        if total_billed_qty > po_ordered_qty:
            raise OverBillingException(
                f"Cumulative Billed Quantity ({total_billed_qty}) for item '{po_desc}' exceeds PO Ordered Quantity ({po_ordered_qty}).",
                details={"item": po_desc, "total_billed": total_billed_qty, "po_ordered": po_ordered_qty}
            ) 