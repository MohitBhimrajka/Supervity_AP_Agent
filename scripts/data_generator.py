#!/usr/bin/env python3
"""
Comprehensive Test Data Generator for AP Automation System
Creates 10 test sets covering various business scenarios for 3-way matching validation.
Uses the correct filename format matching the existing system.
"""

import os
import sys
import random
from datetime import datetime, timedelta

# Add sample_data directory to path to import pdf_templates
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'sample_data'))
from pdf_templates import draw_po_pdf, draw_grn_pdf, draw_invoice_pdf

# Ensure output directory exists
OUTPUT_DIR = "arcelormittal_documents"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def create_test_set_1_perfect_match():
    """Test Set 1: The Perfect Match (Happy Path)"""
    print("Creating Set 1: Perfect Match...")
    
    # PO Data
    po_data = {
        "buyer_name": "TechCorp Manufacturing",
        "buyer_address": "123 Industrial Blvd\nDetroit, MI 48201",
        "vendor_name": "ArcelorMittal",
        "vendor_address": "24-26, Boulevard d'Avranches\nL-1160 Luxembourg",
        "po_number": "PO-78001",
        "order_date": datetime(2024, 1, 15),
        "line_items": [
            {
                "sku": "AM-SB-001",
                "description": "Steel Beam",
                "ordered_qty": 10,
                "unit": "pieces",
                "unit_price": 50.00,
                "line_total": 500.00
            },
            {
                "sku": "AM-RP-002", 
                "description": "Rivet Pack",
                "ordered_qty": 200,
                "unit": "pieces",
                "unit_price": 5.00,
                "line_total": 1000.00
            }
        ],
        "po_subtotal": 1500.00,
        "po_tax": 120.00,
        "po_grand_total": 1620.00
    }
    
    # Create PO PDF
    draw_po_pdf(po_data, f"{OUTPUT_DIR}/Set1_PO-78001.pdf")
    
    # GRN Data
    grn_number = "GRN-84001"
    grn_items = [
        {"sku": "AM-SB-001", "description": "Steel Beam", "received_qty": 10, "unit": "pieces"},
        {"sku": "AM-RP-002", "description": "Rivet Pack", "received_qty": 200, "unit": "pieces"}
    ]
    
    draw_grn_pdf(po_data, grn_number, datetime(2024, 1, 25), grn_items, f"{OUTPUT_DIR}/Set1_{grn_number}_for_PO-78001.pdf")
    
    # Invoice Data
    invoice_number = "INV-AM-98001"
    invoice_data = {**po_data, "grn_number": grn_number, "line_items": [
        {"description": "Steel Beam", "billed_qty": 10, "unit_price": 50.00, "total": 500.00},
        {"description": "Rivet Pack", "billed_qty": 200, "unit_price": 5.00, "total": 1000.00}
    ]}
    
    draw_invoice_pdf(invoice_data, invoice_number, datetime(2024, 1, 26), datetime(2024, 2, 25), f"{OUTPUT_DIR}/Set1_{invoice_number}_for_GRN_GRN-84001.pdf")

def create_test_set_2_price_mismatch():
    """Test Set 2: Price Mismatch (10% over tolerance)"""
    print("Creating Set 2: Price Mismatch...")
    
    po_data = {
        "buyer_name": "Industrial Solutions LLC",
        "buyer_address": "456 Factory Ave\nCleveland, OH 44115",
        "vendor_name": "ArcelorMittal",
        "vendor_address": "24-26, Boulevard d'Avranches\nL-1160 Luxembourg",
        "po_number": "PO-78002",
        "order_date": datetime(2024, 1, 20),
        "line_items": [
            {
                "sku": "AM-CD-003",
                "description": "Cutting Disc",
                "ordered_qty": 50,
                "unit": "pieces",
                "unit_price": 10.00,
                "line_total": 500.00
            }
        ],
        "po_subtotal": 500.00,
        "po_tax": 40.00,
        "po_grand_total": 540.00
    }
    
    draw_po_pdf(po_data, f"{OUTPUT_DIR}/Set2_PO-78002.pdf")
    
    grn_number = "GRN-84002"
    grn_items = [
        {"sku": "AM-CD-003", "description": "Cutting Disc", "received_qty": 50, "unit": "pieces"}
    ]
    
    draw_grn_pdf(po_data, grn_number, datetime(2024, 1, 30), grn_items, f"{OUTPUT_DIR}/Set2_{grn_number}_for_PO-78002.pdf")
    
    # Invoice with 10% price increase
    invoice_number = "INV-AM-98002"
    invoice_data = {**po_data, "grn_number": grn_number, "line_items": [
        {"description": "Cutting Disc", "billed_qty": 50, "unit_price": 11.00, "total": 550.00}  # 10% higher
    ]}
    
    draw_invoice_pdf(invoice_data, invoice_number, datetime(2024, 1, 31), datetime(2024, 3, 1), f"{OUTPUT_DIR}/Set2_{invoice_number}_for_GRN_GRN-84002.pdf")

def create_test_set_3_quantity_mismatch():
    """Test Set 3: Quantity Mismatch (Invoice vs. GRN)"""
    print("Creating Set 3: Quantity Mismatch...")
    
    po_data = {
        "buyer_name": "Safety First Industries",
        "buyer_address": "789 Protection Way\nPhoenix, AZ 85001",
        "vendor_name": "ArcelorMittal",
        "vendor_address": "24-26, Boulevard d'Avranches\nL-1160 Luxembourg",
        "po_number": "PO-78003",
        "order_date": datetime(2024, 1, 25),
        "line_items": [
            {
                "sku": "AM-SG-004",
                "description": "Safety Gloves",
                "ordered_qty": 100,
                "unit": "pairs",
                "unit_price": 15.00,
                "line_total": 1500.00
            }
        ],
        "po_subtotal": 1500.00,
        "po_tax": 120.00,
        "po_grand_total": 1620.00
    }
    
    draw_po_pdf(po_data, f"{OUTPUT_DIR}/Set3_PO-78003.pdf")
    
    grn_number = "GRN-84003"
    grn_items = [
        {"sku": "AM-SG-004", "description": "Safety Gloves", "received_qty": 100, "unit": "pairs"}
    ]
    
    draw_grn_pdf(po_data, grn_number, datetime(2024, 2, 5), grn_items, f"{OUTPUT_DIR}/Set3_{grn_number}_for_PO-78003.pdf")
    
    # Invoice with quantity mismatch (10 more than received)
    invoice_number = "INV-AM-98003"
    invoice_data = {**po_data, "grn_number": grn_number, "line_items": [
        {"description": "Safety Gloves", "billed_qty": 110, "unit_price": 15.00, "total": 1650.00}  # 10 more pairs
    ]}
    
    draw_invoice_pdf(invoice_data, invoice_number, datetime(2024, 2, 6), datetime(2024, 3, 8), f"{OUTPUT_DIR}/Set3_{invoice_number}_for_GRN_GRN-84003.pdf")

def create_test_set_4_partial_shipment():
    """Test Set 4: Partial Shipment & Billing"""
    print("Creating Set 4: Partial Shipment & Billing...")
    
    po_data = {
        "buyer_name": "ElectricWorks Corp",
        "buyer_address": "321 Circuit Dr\nAustin, TX 78701",
        "vendor_name": "ArcelorMittal",
        "vendor_address": "24-26, Boulevard d'Avranches\nL-1160 Luxembourg",
        "po_number": "PO-78004",
        "order_date": datetime(2024, 2, 1),
        "line_items": [
            {
                "sku": "AM-CW-005",
                "description": "Copper Wire",
                "ordered_qty": 500,
                "unit": "meters",
                "unit_price": 2.00,
                "line_total": 1000.00
            }
        ],
        "po_subtotal": 1000.00,
        "po_tax": 80.00,
        "po_grand_total": 1080.00
    }
    
    draw_po_pdf(po_data, f"{OUTPUT_DIR}/Set4_PO-78004.pdf")
    
    # First delivery (300 meters)
    grn1_number = "GRN-84004"
    grn1_items = [
        {"sku": "AM-CW-005", "description": "Copper Wire", "received_qty": 300, "unit": "meters"}
    ]
    
    draw_grn_pdf(po_data, grn1_number, datetime(2024, 2, 10), grn1_items, f"{OUTPUT_DIR}/Set4_{grn1_number}_for_PO-78004.pdf")
    
    invoice1_number = "INV-AM-98004"
    invoice1_data = {**po_data, "grn_number": grn1_number, "line_items": [
        {"description": "Copper Wire", "billed_qty": 300, "unit_price": 2.00, "total": 600.00}
    ]}
    
    draw_invoice_pdf(invoice1_data, invoice1_number, datetime(2024, 2, 11), datetime(2024, 3, 13), f"{OUTPUT_DIR}/Set4_{invoice1_number}_for_GRN_GRN-84004.pdf")
    
    # Second delivery (200 meters)
    grn2_number = "GRN-84005"
    grn2_items = [
        {"sku": "AM-CW-005", "description": "Copper Wire", "received_qty": 200, "unit": "meters"}
    ]
    
    draw_grn_pdf(po_data, grn2_number, datetime(2024, 2, 20), grn2_items, f"{OUTPUT_DIR}/Set4_{grn2_number}_for_PO-78004.pdf")
    
    invoice2_number = "INV-AM-98005"
    invoice2_data = {**po_data, "grn_number": grn2_number, "line_items": [
        {"description": "Copper Wire", "billed_qty": 200, "unit_price": 2.00, "total": 400.00}
    ]}
    
    draw_invoice_pdf(invoice2_data, invoice2_number, datetime(2024, 2, 21), datetime(2024, 3, 23), f"{OUTPUT_DIR}/Set4_{invoice2_number}_for_GRN_GRN-84005.pdf")

def create_test_set_5_item_not_on_po():
    """Test Set 5: Item Not on PO/GRN (Scope Creep)"""
    print("Creating Set 5: Item Not on PO/GRN...")
    
    po_data = {
        "buyer_name": "WeldMaster Industries",
        "buyer_address": "654 Fabrication St\nHouston, TX 77001",
        "vendor_name": "ArcelorMittal",
        "vendor_address": "24-26, Boulevard d'Avranches\nL-1160 Luxembourg",
        "po_number": "PO-78005",
        "order_date": datetime(2024, 2, 5),
        "line_items": [
            {
                "sku": "AM-WM-006",
                "description": "Welding Machine",
                "ordered_qty": 1,
                "unit": "pieces",
                "unit_price": 1200.00,
                "line_total": 1200.00
            }
        ],
        "po_subtotal": 1200.00,
        "po_tax": 96.00,
        "po_grand_total": 1296.00
    }
    
    draw_po_pdf(po_data, f"{OUTPUT_DIR}/Set5_PO-78005.pdf")
    
    grn_number = "GRN-84006"
    grn_items = [
        {"sku": "AM-WM-006", "description": "Welding Machine", "received_qty": 1, "unit": "pieces"}
    ]
    
    draw_grn_pdf(po_data, grn_number, datetime(2024, 2, 15), grn_items, f"{OUTPUT_DIR}/Set5_{grn_number}_for_PO-78005.pdf")
    
    # Invoice with unauthorized additional item
    invoice_number = "INV-AM-98006"
    invoice_data = {**po_data, "grn_number": grn_number, "line_items": [
        {"description": "Welding Machine", "billed_qty": 1, "unit_price": 1200.00, "total": 1200.00},
        {"description": "Expedited Shipping Fee", "billed_qty": 1, "unit_price": 75.00, "total": 75.00}  # Not on PO/GRN
    ]}
    
    draw_invoice_pdf(invoice_data, invoice_number, datetime(2024, 2, 16), datetime(2024, 3, 18), f"{OUTPUT_DIR}/Set5_{invoice_number}_for_GRN_GRN-84006.pdf")

def create_test_set_6_missing_grn():
    """Test Set 6: Missing Document (Incomplete Set)"""
    print("Creating Set 6: Missing GRN...")
    
    po_data = {
        "buyer_name": "Precision Tools Ltd",
        "buyer_address": "987 Machinery Rd\nChicago, IL 60601",
        "vendor_name": "ArcelorMittal",
        "vendor_address": "24-26, Boulevard d'Avranches\nL-1160 Luxembourg",
        "po_number": "PO-78006",
        "order_date": datetime(2024, 2, 10),
        "line_items": [
            {
                "sku": "AM-DP-007",
                "description": "Drill Press",
                "ordered_qty": 1,
                "unit": "pieces",
                "unit_price": 800.00,
                "line_total": 800.00
            }
        ],
        "po_subtotal": 800.00,
        "po_tax": 64.00,
        "po_grand_total": 864.00
    }
    
    draw_po_pdf(po_data, f"{OUTPUT_DIR}/Set6_PO-78006.pdf")
    
    # Create invoice that references missing GRN-84007 (but don't create the GRN)
    missing_grn_number = "GRN-84007"
    invoice_number = "INV-AM-98007"
    invoice_data = {**po_data, "grn_number": missing_grn_number, "line_items": [
        {"description": "Drill Press", "billed_qty": 1, "unit_price": 800.00, "total": 800.00}
    ]}
    
    draw_invoice_pdf(invoice_data, invoice_number, datetime(2024, 2, 20), datetime(2024, 3, 22), f"{OUTPUT_DIR}/Set6_{invoice_number}_for_GRN_GRN-84007.pdf")
    # Note: GRN-84007 is intentionally not created to test missing document scenario

def create_test_set_7_duplicate_invoice():
    """Test Set 7: Duplicate Invoice Detection"""
    print("Creating Set 7: Duplicate Invoice...")
    
    po_data = {
        "buyer_name": "MetalWorks Assembly",
        "buyer_address": "147 Assembly Line\nSeattle, WA 98101",
        "vendor_name": "ArcelorMittal",
        "vendor_address": "24-26, Boulevard d'Avranches\nL-1160 Luxembourg",
        "po_number": "PO-78007",
        "order_date": datetime(2024, 2, 15),
        "line_items": [
            {
                "sku": "AM-SP-008",
                "description": "Steel Plate",
                "ordered_qty": 25,
                "unit": "pieces",
                "unit_price": 120.00,
                "line_total": 3000.00
            }
        ],
        "po_subtotal": 3000.00,
        "po_tax": 240.00,
        "po_grand_total": 3240.00
    }
    
    draw_po_pdf(po_data, f"{OUTPUT_DIR}/Set7_PO-78007.pdf")
    
    grn_number = "GRN-84008"
    grn_items = [
        {"sku": "AM-SP-008", "description": "Steel Plate", "received_qty": 25, "unit": "pieces"}
    ]
    
    draw_grn_pdf(po_data, grn_number, datetime(2024, 2, 25), grn_items, f"{OUTPUT_DIR}/Set7_{grn_number}_for_PO-78007.pdf")
    
    # Create two identical invoices (duplicate scenario)
    invoice_data = {**po_data, "grn_number": grn_number, "line_items": [
        {"description": "Steel Plate", "billed_qty": 25, "unit_price": 120.00, "total": 3000.00}
    ]}
    
    invoice1_number = "INV-AM-98008"
    invoice2_number = "INV-AM-98009"
    
    draw_invoice_pdf(invoice_data, invoice1_number, datetime(2024, 2, 26), datetime(2024, 3, 28), f"{OUTPUT_DIR}/Set7_{invoice1_number}_for_GRN_GRN-84008.pdf")
    draw_invoice_pdf(invoice_data, invoice2_number, datetime(2024, 2, 26), datetime(2024, 3, 28), f"{OUTPUT_DIR}/Set7_{invoice2_number}_for_GRN_GRN-84008.pdf")

def create_test_set_8_currency_mismatch():
    """Test Set 8: Currency/Unit Conversion Issues"""
    print("Creating Set 8: Currency/Unit Issues...")
    
    po_data = {
        "buyer_name": "Global Manufacturing Inc",
        "buyer_address": "258 International Blvd\nMiami, FL 33101",
        "vendor_name": "ArcelorMittal",
        "vendor_address": "24-26, Boulevard d'Avranches\nL-1160 Luxembourg",
        "po_number": "PO-78008",
        "order_date": datetime(2024, 2, 20),
        "line_items": [
            {
                "sku": "AM-AC-009",
                "description": "Aluminum Coil",
                "ordered_qty": 2,
                "unit": "tons",
                "unit_price": 1800.00,
                "line_total": 3600.00
            }
        ],
        "po_subtotal": 3600.00,
        "po_tax": 288.00,
        "po_grand_total": 3888.00
    }
    
    draw_po_pdf(po_data, f"{OUTPUT_DIR}/Set8_PO-78008.pdf")
    
    grn_number = "GRN-84009"
    grn_items = [
        {"sku": "AM-AC-009", "description": "Aluminum Coil", "received_qty": 2000, "unit": "kg"}  # Different unit
    ]
    
    draw_grn_pdf(po_data, grn_number, datetime(2024, 3, 1), grn_items, f"{OUTPUT_DIR}/Set8_{grn_number}_for_PO-78008.pdf")
    
    # Invoice with yet another unit variation
    invoice_number = "INV-AM-98010"
    invoice_data = {**po_data, "grn_number": grn_number, "line_items": [
        {"description": "Aluminum Coil", "billed_qty": 4409, "unit_price": 0.82, "total": 3615.38}  # Price in different currency/unit
    ]}
    
    draw_invoice_pdf(invoice_data, invoice_number, datetime(2024, 3, 2), datetime(2024, 4, 1), f"{OUTPUT_DIR}/Set8_{invoice_number}_for_GRN_GRN-84009.pdf")

def create_test_set_9_multi_line_complex():
    """Test Set 9: Complex Multi-Line with Mixed Issues"""
    print("Creating Set 9: Complex Multi-Line Issues...")
    
    po_data = {
        "buyer_name": "Advanced Materials Corp",
        "buyer_address": "369 Innovation Way\nBoston, MA 02101",
        "vendor_name": "ArcelorMittal",
        "vendor_address": "24-26, Boulevard d'Avranches\nL-1160 Luxembourg",
        "po_number": "PO-78009",
        "order_date": datetime(2024, 2, 25),
        "line_items": [
            {
                "sku": "AM-HB-010",
                "description": "H-Beam Steel",
                "ordered_qty": 50,
                "unit": "pieces",
                "unit_price": 85.00,
                "line_total": 4250.00
            },
            {
                "sku": "AM-BB-011",
                "description": "Bolt Bundle",
                "ordered_qty": 100,
                "unit": "sets",
                "unit_price": 25.00,
                "line_total": 2500.00
            },
            {
                "sku": "AM-WP-012",
                "description": "Washer Pack",
                "ordered_qty": 200,
                "unit": "packs",
                "unit_price": 8.00,
                "line_total": 1600.00
            }
        ],
        "po_subtotal": 8350.00,
        "po_tax": 668.00,
        "po_grand_total": 9018.00
    }
    
    draw_po_pdf(po_data, f"{OUTPUT_DIR}/Set9_PO-78009.pdf")
    
    grn_number = "GRN-84010"
    grn_items = [
        {"sku": "AM-HB-010", "description": "H-Beam Steel", "received_qty": 50, "unit": "pieces"},
        {"sku": "AM-BB-011", "description": "Bolt Bundle", "received_qty": 95, "unit": "sets"},  # 5 short
        {"sku": "AM-WP-012", "description": "Washer Pack", "received_qty": 200, "unit": "packs"}
    ]
    
    draw_grn_pdf(po_data, grn_number, datetime(2024, 3, 5), grn_items, f"{OUTPUT_DIR}/Set9_{grn_number}_for_PO-78009.pdf")
    
    # Invoice with mixed issues: price mismatch on item 1, quantity matches GRN for item 2, missing item 3
    invoice_number = "INV-AM-98011"
    invoice_data = {**po_data, "grn_number": grn_number, "line_items": [
        {"description": "H-Beam Steel", "billed_qty": 50, "unit_price": 92.00, "total": 4600.00},  # Price increase
        {"description": "Bolt Bundle", "billed_qty": 95, "unit_price": 25.00, "total": 2375.00},   # Matches GRN
        # Missing Washer Pack line - partial invoice
    ]}
    
    draw_invoice_pdf(invoice_data, invoice_number, datetime(2024, 3, 6), datetime(2024, 4, 5), f"{OUTPUT_DIR}/Set9_{invoice_number}_for_GRN_GRN-84010.pdf")

def create_test_set_10_timing_issues():
    """Test Set 10: Timing and Workflow Issues"""
    print("Creating Set 10: Timing Issues...")
    
    po_data = {
        "buyer_name": "Rapid Delivery Systems",
        "buyer_address": "741 Logistics Lane\nDallas, TX 75201",
        "vendor_name": "ArcelorMittal",
        "vendor_address": "24-26, Boulevard d'Avranches\nL-1160 Luxembourg",
        "po_number": "PO-78010",
        "order_date": datetime(2024, 3, 1),
        "line_items": [
            {
                "sku": "AM-FT-013",
                "description": "Fastener Set",
                "ordered_qty": 500,
                "unit": "pieces",
                "unit_price": 3.50,
                "line_total": 1750.00
            }
        ],
        "po_subtotal": 1750.00,
        "po_tax": 140.00,
        "po_grand_total": 1890.00
    }
    
    draw_po_pdf(po_data, f"{OUTPUT_DIR}/Set10_PO-78010.pdf")
    
    grn_number = "GRN-84011"
    grn_items = [
        {"sku": "AM-FT-013", "description": "Fastener Set", "received_qty": 500, "unit": "pieces"}
    ]
    
    # GRN created BEFORE PO date (timing issue)
    draw_grn_pdf(po_data, grn_number, datetime(2024, 2, 25), grn_items, f"{OUTPUT_DIR}/Set10_{grn_number}_for_PO-78010.pdf")
    
    # Invoice created before GRN (workflow violation)
    invoice_number = "INV-AM-98012"
    invoice_data = {**po_data, "grn_number": grn_number, "line_items": [
        {"description": "Fastener Set", "billed_qty": 500, "unit_price": 3.50, "total": 1750.00}
    ]}
    
    # Invoice dated before GRN
    draw_invoice_pdf(invoice_data, invoice_number, datetime(2024, 2, 20), datetime(2024, 3, 22), f"{OUTPUT_DIR}/Set10_{invoice_number}_for_GRN_GRN-84011.pdf")

def create_test_set_11_multi_po_invoice():
    """Test Set 11: A single invoice covering items from two different POs."""
    print("Creating Set 11: Multi-PO Invoice...")

    # --- PO #1 Data ---
    po1_data = {
        "buyer_name": "Multi-System Builders",
        "buyer_address": "101 Integration Ave\nSan Francisco, CA 94105",
        "vendor_name": "ArcelorMittal",
        "vendor_address": "24-26, Boulevard d'Avranches\nL-1160 Luxembourg",
        "po_number": "PO-78011",
        "order_date": datetime(2024, 3, 10),
        "line_items": [
            {"sku": "AM-SB-001", "description": "Steel Beam", "ordered_qty": 20, "unit": "pieces", "unit_price": 55.00, "line_total": 1100.00}
        ],
        "po_subtotal": 1100.00, "po_tax": 88.00, "po_grand_total": 1188.00
    }
    draw_po_pdf(po1_data, f"{OUTPUT_DIR}/Set11_PO-78011.pdf")
    
    # --- PO #2 Data ---
    po2_data = {
        "buyer_name": "Multi-System Builders",
        "buyer_address": "101 Integration Ave\nSan Francisco, CA 94105",
        "vendor_name": "ArcelorMittal",
        "vendor_address": "24-26, Boulevard d'Avranches\nL-1160 Luxembourg",
        "po_number": "PO-78012",
        "order_date": datetime(2024, 3, 12),
        "line_items": [
            {"sku": "AM-RP-002", "description": "Rivet Pack", "ordered_qty": 50, "unit": "pieces", "unit_price": 6.00, "line_total": 300.00}
        ],
        "po_subtotal": 300.00, "po_tax": 24.00, "po_grand_total": 324.00
    }
    draw_po_pdf(po2_data, f"{OUTPUT_DIR}/Set11_PO-78012.pdf")

    # --- Consolidated Invoice Data ---
    invoice_number = "INV-AM-98013"
    consolidated_invoice_data = {
        "buyer_name": "Multi-System Builders",
        "buyer_address": "101 Integration Ave\nSan Francisco, CA 94105",
        "vendor_name": "ArcelorMittal",
        "vendor_address": "24-26, Boulevard d'Avranches\nL-1160 Luxembourg",
        # CRITICAL: This invoice references both POs.
        "related_po_numbers": ["PO-78011", "PO-78012"],
        "related_grn_numbers": [], # Assuming no GRN for simplicity
        "line_items": [
            # Item from PO1, note the line-item specific po_number
            {"description": "Steel Beam", "billed_qty": 20, "unit_price": 55.00, "total": 1100.00, "po_number": "PO-78011"},
            # Item from PO2
            {"description": "Rivet Pack", "billed_qty": 50, "unit_price": 6.00, "total": 300.00, "po_number": "PO-78012"},
        ],
        "subtotal": 1400.00,
        "tax": 112.00,
        "grand_total": 1512.00
    }
    # The filename doesn't need to reference the POs, but the content does.
    draw_invoice_pdf(consolidated_invoice_data, invoice_number, datetime(2024, 3, 20), datetime(2024, 4, 19), f"{OUTPUT_DIR}/Set11_{invoice_number}_for_MultiPO.pdf")

def main():
    """Generate all 10 test sets"""
    print("🧪 COMPREHENSIVE AP AUTOMATION TEST DATA GENERATOR")
    print("=" * 60)
    print("Generating 10 test sets with correct filename format...")
    print(f"Output directory: {OUTPUT_DIR}/")
    print("=" * 60)
    
    # Create all test sets
    create_test_set_1_perfect_match()
    create_test_set_2_price_mismatch()
    create_test_set_3_quantity_mismatch()
    create_test_set_4_partial_shipment()
    create_test_set_5_item_not_on_po()
    create_test_set_6_missing_grn()
    create_test_set_7_duplicate_invoice()
    create_test_set_8_currency_mismatch()
    create_test_set_9_multi_line_complex()
    create_test_set_10_timing_issues()
    create_test_set_11_multi_po_invoice()
    
    print("\n" + "=" * 60)
    print("✅ TEST DATA GENERATION COMPLETE!")
    print("=" * 60)
    print(f"📁 Location: {OUTPUT_DIR}/")
    print("\n📋 Filename Format Used:")
    print("  - POs: SetX_PO-XXXXX.pdf")
    print("  - GRNs: SetX_GRN-XXXXX_for_PO-XXXXX.pdf")
    print("  - Invoices: SetX_INV-AM-XXXXX_for_GRN_GRN-XXXXX.pdf")
    
    print("\n📋 Test Scenarios Created:")
    print("  1. Perfect Match (Happy Path)")
    print("  2. Price Mismatch (10% over tolerance)")
    print("  3. Quantity Mismatch (Invoice vs GRN)")
    print("  4. Partial Shipment & Billing")
    print("  5. Item Not on PO/GRN (Scope Creep)")
    print("  6. Missing Document (No GRN)")
    print("  7. Duplicate Invoice Detection")
    print("  8. Currency/Unit Conversion Issues")
    print("  9. Complex Multi-Line with Mixed Issues")
    print(" 10. Timing and Workflow Issues")
    print(" 11. Multi-PO Invoice")
    
    print("\n🔄 Next Steps:")
    print("1. Run: python cleanup_db.py (in Tungsten_AP_Agent directory)")
    print("2. Start your backend and frontend")
    print("3. Click 'Load & Process Documents' in the UI")
    print("4. Review results in Dashboard → Review Queue → Data Explorer")
    
    print("\n💡 Expected Results:")
    print("  ✅ Set 1: All matched, no exceptions")
    print("  ❌ Sets 2-11: Various exceptions for testing AI diagnosis")

if __name__ == "__main__":
    main() 