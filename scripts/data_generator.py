#!/usr/bin/env python3
"""
DEFINITIVE Test Data Generator for Supervity AP Command Center
Creates 12 advanced test sets covering complex business scenarios for a robust demo.
"""
import os
import sys
from datetime import datetime, timedelta

# Add sample_data directory to path to import pdf_templates
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'sample_data'))
from pdf_templates import draw_po_pdf, draw_grn_pdf, draw_invoice_pdf

# Ensure output directory exists and is correctly located
SAMPLE_DATA_DIR = "sample_data"
OUTPUT_DIR = os.path.join(SAMPLE_DATA_DIR, "arcelormittal_documents")
os.makedirs(SAMPLE_DATA_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# --- VENDOR & BUYER DEFINITIONS ---
ARCDETAILS = {"name": "ArcelorMittal", "address": "24-26, Boulevard d'Avranches\nL-1160 Luxembourg"}
GTDETAILS = {"name": "Global Tech Supplies", "address": "789 Innovation Drive\nSilicon Valley, CA 94043"}
CONSULTDETAILS = {"name": "Innovate Consulting", "address": "456 Strategy Blvd\nNew York, NY 10001"}
BUYERDETAILS = {"name": "Supervity Inc", "address": "123 Automation Lane\nFuture City, FC 54321"}

# --- HELPER TO STANDARDIZE DATA ---
def get_base_data(vendor_details, po_number, order_date):
    return {
        "buyer_name": BUYERDETAILS["name"], "buyer_address": BUYERDETAILS["address"],
        "vendor_name": vendor_details["name"], "vendor_address": vendor_details["address"],
        "po_number": po_number, "order_date": order_date
    }

def calculate_totals(line_items):
    subtotal = sum(item.get('line_total', 0) for item in line_items)
    tax = subtotal * 0.08  # Standard 8% tax
    grand_total = subtotal + tax
    return {"po_subtotal": subtotal, "po_tax": tax, "po_grand_total": grand_total}

# --- TEST SETS ---

def set_1_perfect_match_clean_vendor():
    print("  1. Perfect Match (Clean Vendor)...")
    po_data = get_base_data(GTDETAILS, "PO-GT-1001", datetime(2024, 3, 1))
    line_items = [
        {"sku": "GT-CBL-01", "description": "USB-C Cable Pack", "ordered_qty": 50, "unit": "packs", "unit_price": 25.00, "line_total": 1250.00},
        {"sku": "GT-MSE-05", "description": "Ergonomic Mouse", "ordered_qty": 20, "unit": "pieces", "unit_price": 45.00, "line_total": 900.00}
    ]
    po_data.update(calculate_totals(line_items))
    po_data["line_items"] = line_items
    draw_po_pdf(po_data, f"{OUTPUT_DIR}/Set01_PO-GT-1001.pdf")
    
    grn_items = [{"sku": "GT-CBL-01", "description": "USB-C Cable Pack", "received_qty": 50, "unit": "packs"}, {"sku": "GT-MSE-05", "description": "Ergonomic Mouse", "received_qty": 20, "unit": "pieces"}]
    draw_grn_pdf(po_data, "GRN-GT-1001", datetime(2024, 3, 10), grn_items, f"{OUTPUT_DIR}/Set01_GRN-GT-1001.pdf")

    inv_line_items = [
        {"description": "USB-C Cable Pack", "billed_qty": 50, "unit_price": 25.00, "total": 1250.00, "unit": "packs"},
        {"description": "Ergonomic Mouse", "billed_qty": 20, "unit_price": 45.00, "total": 900.00, "unit": "pieces"}
    ]
    inv_data = {**po_data, "related_grn_numbers": ["GRN-GT-1001"], "line_items": inv_line_items}
    draw_invoice_pdf(inv_data, "INV-GT-5001", datetime(2024, 3, 11), datetime(2024, 4, 10), f"{OUTPUT_DIR}/Set01_INV-GT-5001.pdf")

def set_2_price_mismatch_for_demo():
    print("  2. Price Mismatch (Demo Scenario)...")
    po_data = get_base_data(ARCDETAILS, "PO-AM-78002", datetime(2024, 3, 5))
    line_items = [{"sku": "AM-CD-003", "description": "Cutting Disc", "ordered_qty": 50, "unit": "pieces", "unit_price": 10.00, "line_total": 500.00}]
    po_data.update(calculate_totals(line_items))
    po_data["line_items"] = line_items
    draw_po_pdf(po_data, f"{OUTPUT_DIR}/Set02_PO-AM-78002.pdf")

    grn_items = [{"sku": "AM-CD-003", "description": "Cutting Disc", "received_qty": 50, "unit": "pieces"}]
    draw_grn_pdf(po_data, "GRN-AM-84002", datetime(2024, 3, 15), grn_items, f"{OUTPUT_DIR}/Set02_GRN-AM-84002.pdf")

    inv_line_items = [{"description": "Cutting Disc", "billed_qty": 50, "unit_price": 11.00, "total": 550.00, "unit": "pieces"}]
    inv_data = {**po_data, "related_grn_numbers": ["GRN-AM-84002"], "line_items": inv_line_items}
    draw_invoice_pdf(inv_data, "INV-AM-98002", datetime(2024, 3, 16), datetime(2024, 4, 15), f"{OUTPUT_DIR}/Set02_INV-AM-98002.pdf")

def set_3_mixed_line_item_issue():
    print("  3. Mixed Line Item Issues...")
    po_data = get_base_data(ARCDETAILS, "PO-AM-78003", datetime(2024, 3, 8))
    line_items = [
        {"sku": "AM-SG-004", "description": "Safety Gloves", "ordered_qty": 100, "unit": "pairs", "unit_price": 15.00, "line_total": 1500.00},
        {"sku": "AM-HH-005", "description": "Hard Hat", "ordered_qty": 20, "unit": "pieces", "unit_price": 22.00, "line_total": 440.00}
    ]
    po_data.update(calculate_totals(line_items))
    po_data["line_items"] = line_items
    draw_po_pdf(po_data, f"{OUTPUT_DIR}/Set03_PO-AM-78003.pdf")

    grn_items = [{"sku": "AM-SG-004", "description": "Safety Gloves", "received_qty": 95, "unit": "pairs"}, {"sku": "AM-HH-005", "description": "Hard Hat", "received_qty": 20, "unit": "pieces"}]
    draw_grn_pdf(po_data, "GRN-AM-84003", datetime(2024, 3, 18), grn_items, f"{OUTPUT_DIR}/Set03_GRN-AM-84003.pdf")

    inv_line_items = [
        {"description": "Safety Gloves", "billed_qty": 95, "unit_price": 15.00, "total": 1425.00, "unit": "pairs"}, # OK
        {"description": "Hard Hat", "billed_qty": 21, "unit_price": 22.00, "total": 462.00, "unit": "pieces"}   # BAD
    ]
    inv_data = {**po_data, "related_grn_numbers": ["GRN-AM-84003"], "line_items": inv_line_items}
    draw_invoice_pdf(inv_data, "INV-AM-98003", datetime(2024, 3, 19), datetime(2024, 4, 18), f"{OUTPUT_DIR}/Set03_INV-AM-98003.pdf")

def set_4_multi_grn_to_invoice():
    print("  4. Multi-GRN to Single Invoice...")
    po_data = get_base_data(ARCDETAILS, "PO-AM-78004", datetime(2024, 3, 12))
    line_items = [{"sku": "AM-CW-005", "description": "Copper Wire", "ordered_qty": 500, "unit": "meters", "unit_price": 2.00, "line_total": 1000.00}]
    po_data.update(calculate_totals(line_items))
    po_data["line_items"] = line_items
    draw_po_pdf(po_data, f"{OUTPUT_DIR}/Set04_PO-AM-78004.pdf")
    
    draw_grn_pdf(po_data, "GRN-AM-84004-A", datetime(2024, 3, 20), [{"sku": "AM-CW-005", "description": "Copper Wire", "received_qty": 300, "unit": "meters"}], f"{OUTPUT_DIR}/Set04_GRN-AM-84004-A.pdf")
    draw_grn_pdf(po_data, "GRN-AM-84004-B", datetime(2024, 3, 25), [{"sku": "AM-CW-005", "description": "Copper Wire", "received_qty": 200, "unit": "meters"}], f"{OUTPUT_DIR}/Set04_GRN-AM-84004-B.pdf")

    inv_line_items = [{"description": "Copper Wire", "billed_qty": 500, "unit_price": 2.00, "total": 1000.00, "unit": "meters"}]
    inv_data = {**po_data, "related_grn_numbers": ["GRN-AM-84004-A", "GRN-AM-84004-B"], "line_items": inv_line_items}
    draw_invoice_pdf(inv_data, "INV-AM-98004", datetime(2024, 3, 26), datetime(2024, 4, 25), f"{OUTPUT_DIR}/Set04_INV-AM-98004.pdf")
    
def set_5_multi_po_to_invoice():
    print("  5. Multi-PO to Single Invoice...")
    po1 = get_base_data(ARCDETAILS, "PO-AM-78005-A", datetime(2024, 3, 15))
    po1_li = [{"sku": "AM-SP-008", "description": "Steel Plate", "ordered_qty": 25, "unit": "pieces", "unit_price": 120.00, "line_total": 3000.00}]
    po1.update(calculate_totals(po1_li)); po1["line_items"] = po1_li
    draw_po_pdf(po1, f"{OUTPUT_DIR}/Set05_PO-AM-78005-A.pdf")
    
    po2 = get_base_data(ARCDETAILS, "PO-AM-78005-B", datetime(2024, 3, 16))
    po2_li = [{"sku": "AM-RB-009", "description": "Rivet Bundle", "ordered_qty": 5, "unit": "sets", "unit_price": 150.00, "line_total": 750.00}]
    po2.update(calculate_totals(po2_li)); po2["line_items"] = po2_li
    draw_po_pdf(po2, f"{OUTPUT_DIR}/Set05_PO-AM-78005-B.pdf")
    
    inv_line_items = [
        {"description": "Steel Plate", "po_number": "PO-AM-78005-A", "billed_qty": 25, "unit_price": 120.00, "total": 3000.00, "unit": "pieces"},
        {"description": "Rivet Bundle", "po_number": "PO-AM-78005-B", "billed_qty": 5, "unit_price": 150.00, "total": 750.00, "unit": "sets"}
    ]
    inv_data = {**po1, "related_po_numbers": ["PO-AM-78005-A", "PO-AM-78005-B"], "line_items": inv_line_items}
    draw_invoice_pdf(inv_data, "INV-AM-98005", datetime(2024, 3, 28), datetime(2024, 4, 27), f"{OUTPUT_DIR}/Set05_INV-AM-98005.pdf")

def set_6_non_po_service_invoice():
    print("  6. Non-PO Service Invoice...")
    inv_line_items = [{"description": "Q1 Strategy Consulting Services", "billed_qty": 1, "unit_price": 5000.00, "total": 5000.00, "unit": "service"}]
    inv_data = {**get_base_data(CONSULTDETAILS, "", datetime(2024,4,1)), "line_items": inv_line_items, "related_po_numbers": []}
    draw_invoice_pdf(inv_data, "INV-IC-2024-01", datetime(2024, 4, 1), datetime(2024, 4, 30), f"{OUTPUT_DIR}/Set06_INV-IC-2024-01_NonPO.pdf")

def set_7_unit_conversion_issue():
    print("  7. Unit Conversion (tons/kg/lbs)...")
    po_data = get_base_data(ARCDETAILS, "PO-AM-78008", datetime(2024, 2, 20))
    line_items = [{"sku": "AM-AC-009", "description": "Aluminum Coil", "ordered_qty": 2, "unit": "tons", "unit_price": 1800.00, "line_total": 3600.00}]
    po_data.update(calculate_totals(line_items)); po_data["line_items"] = line_items
    draw_po_pdf(po_data, f"{OUTPUT_DIR}/Set07_PO-AM-78008.pdf")
    
    grn_items = [{"sku": "AM-AC-009", "description": "Aluminum Coil", "received_qty": 2000, "unit": "kg"}]
    draw_grn_pdf(po_data, "GRN-AM-84009", datetime(2024, 3, 1), grn_items, f"{OUTPUT_DIR}/Set07_GRN-AM-84009.pdf")
    
    inv_line_items = [{"description": "Aluminum Coil", "billed_qty": 4409, "unit_price": 0.82, "total": 3615.38, "unit": "lbs"}]
    inv_data = {**po_data, "related_grn_numbers": ["GRN-AM-84009"], "line_items": inv_line_items}
    draw_invoice_pdf(inv_data, "INV-AM-98010", datetime(2024, 3, 2), datetime(2024, 4, 1), f"{OUTPUT_DIR}/Set07_INV-AM-98010.pdf")

def set_8_financial_mismatch():
    print("  8. Financial Calculation Mismatch...")
    po_data = get_base_data(ARCDETAILS, "PO-AM-78009", datetime(2024, 4, 5))
    line_items = [{"sku": "AM-WP-012", "description": "Washer Pack", "ordered_qty": 200, "unit": "packs", "unit_price": 8.00, "line_total": 1600.00}]
    po_data.update(calculate_totals(line_items)); po_data["line_items"] = line_items
    draw_po_pdf(po_data, f"{OUTPUT_DIR}/Set08_PO-AM-78009.pdf")
    
    inv_line_items = [{"description": "Washer Pack", "billed_qty": 200, "unit_price": 8.00, "total": 1600.00, "unit": "packs"}]
    inv_data = {**po_data, "line_items": inv_line_items}
    draw_invoice_pdf(inv_data, "INV-AM-98011", datetime(2024, 4, 10), datetime(2024, 5, 10), f"{OUTPUT_DIR}/Set08_INV-AM-98011.pdf")

def set_9_timing_violation():
    print("  9. Timing Violation (Invoice before PO)...")
    po_data = get_base_data(ARCDETAILS, "PO-AM-78010", datetime(2024, 4, 15))
    line_items = [{"sku": "AM-FT-013", "description": "Fastener Set", "ordered_qty": 500, "unit": "pieces", "unit_price": 3.50, "line_total": 1750.00}]
    po_data.update(calculate_totals(line_items)); po_data["line_items"] = line_items
    draw_po_pdf(po_data, f"{OUTPUT_DIR}/Set09_PO-AM-78010.pdf")
    
    inv_line_items = [{"description": "Fastener Set", "billed_qty": 500, "unit_price": 3.50, "total": 1750.00, "unit": "pieces"}]
    inv_data = {**po_data, "line_items": inv_line_items}
    # Invoice date is BEFORE PO date
    draw_invoice_pdf(inv_data, "INV-AM-98012", datetime(2024, 4, 14), datetime(2024, 5, 14), f"{OUTPUT_DIR}/Set09_INV-AM-98012.pdf")

def set_10_and_11_volume_data():
    print(" 10. Volume Data (Perfect Matches)...")
    # GT Invoice 1
    po_data_1 = get_base_data(GTDETAILS, "PO-GT-1002", datetime(2024, 4, 2))
    li_1 = [{"sku": "GT-KB-02", "description": "Mechanical Keyboard", "ordered_qty": 15, "unit": "units", "unit_price": 120.00, "line_total": 1800.00}]
    po_data_1.update(calculate_totals(li_1)); po_data_1["line_items"] = li_1
    draw_po_pdf(po_data_1, f"{OUTPUT_DIR}/Set10_PO-GT-1002.pdf")
    
    inv_1_line_items = [{"description": "Mechanical Keyboard", "billed_qty": 15, "unit_price": 120.00, "total": 1800.00, "unit": "units"}]
    inv_1_data = {**po_data_1, "line_items": inv_1_line_items}
    draw_invoice_pdf(inv_1_data, "INV-GT-5002", datetime(2024, 4, 3), datetime(2024, 5, 3), f"{OUTPUT_DIR}/Set10_INV-GT-5002.pdf")

    # GT Invoice 2
    po_data_2 = get_base_data(GTDETAILS, "PO-GT-1003", datetime(2024, 4, 5))
    li_2 = [{"sku": "GT-MON-27", "description": "27-inch Monitor", "ordered_qty": 10, "unit": "units", "unit_price": 350.00, "line_total": 3500.00}]
    po_data_2.update(calculate_totals(li_2)); po_data_2["line_items"] = li_2
    draw_po_pdf(po_data_2, f"{OUTPUT_DIR}/Set11_PO-GT-1003.pdf")
    
    inv_2_line_items = [{"description": "27-inch Monitor", "billed_qty": 10, "unit_price": 350.00, "total": 3500.00, "unit": "units"}]
    inv_2_data = {**po_data_2, "line_items": inv_2_line_items}
    draw_invoice_pdf(inv_2_data, "INV-GT-5003", datetime(2024, 4, 6), datetime(2024, 5, 6), f"{OUTPUT_DIR}/Set11_INV-GT-5003.pdf")

def set_12_duplicate_invoice():
    print(" 12. Duplicate Invoice (Slight Variation)...")
    po_data = get_base_data(ARCDETAILS, "PO-AM-78011", datetime(2024, 4, 20))
    line_items = [{"sku": "AM-BEAM-S", "description": "Small I-Beam", "ordered_qty": 40, "unit": "pieces", "unit_price": 75.00, "line_total": 3000.00}]
    po_data.update(calculate_totals(line_items)); po_data["line_items"] = line_items
    draw_po_pdf(po_data, f"{OUTPUT_DIR}/Set12_PO-AM-78011.pdf")
    
    # First invoice
    inv_line_items = [{"description": "Small I-Beam", "billed_qty": 40, "unit_price": 75.00, "total": 3000.00, "unit": "pieces"}]
    inv_data = {**po_data, "line_items": inv_line_items}
    draw_invoice_pdf(inv_data, "INV-AM-98013", datetime(2024, 4, 22), datetime(2024, 5, 22), f"{OUTPUT_DIR}/Set12_INV-AM-98013.pdf")
    # Second invoice, same content, slightly different ID
    draw_invoice_pdf(inv_data, "INV-AM-98013-DUP", datetime(2024, 4, 22), datetime(2024, 5, 22), f"{OUTPUT_DIR}/Set12_INV-AM-98013-DUP.pdf")

def main():
    """Generate all test sets"""
    print("🧪 Supervity AP Test Data Generator (v2)")
    print("=" * 60)
    print(f"Output directory: {OUTPUT_DIR}/")
    
    if os.path.exists(OUTPUT_DIR):
        for f in os.listdir(OUTPUT_DIR):
            os.remove(os.path.join(OUTPUT_DIR, f))
    print("🧹 Cleaned output directory.")
    print("=" * 60)

    # Call all generation functions
    set_1_perfect_match_clean_vendor()
    set_2_price_mismatch_for_demo()
    set_3_mixed_line_item_issue()
    set_4_multi_grn_to_invoice()
    set_5_multi_po_to_invoice()
    set_6_non_po_service_invoice()
    set_7_unit_conversion_issue()
    set_8_financial_mismatch()
    set_9_timing_violation()
    set_10_and_11_volume_data()
    set_12_duplicate_invoice()

    print("\n" + "=" * 60)
    print("✅ All 12 test sets generated successfully!")
    print("\n🔄 Next Steps:")
    print("  1. Run: python run_fresh.py")
    print("  2. Start your frontend: npm run dev")
    print("  3. In the Data Center, click 'Sync Sample Data'")

if __name__ == "__main__":
    main() 