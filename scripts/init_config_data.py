#!/usr/bin/env python3
"""
Initialize sample configuration data for the AP system.
This script adds sample vendor settings and automation rules to demonstrate
the configuration functionality.
"""

import os
import sys

# Add both the project root and src directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
src_dir = os.path.join(project_root, 'src')
sys.path.insert(0, project_root)
sys.path.insert(0, src_dir)

from app.db.session import SessionLocal
from app.db import models

def create_sample_vendor_settings():
    """Create sample vendor settings."""
    print("🏢 Creating sample vendor settings...")
    db = SessionLocal()
    
    try:
        # Check if vendor settings already exist
        existing_count = db.query(models.VendorSetting).count()
        if existing_count > 0:
            print(f"⚠️ Found {existing_count} existing vendor settings. Skipping creation.")
            return
        
        sample_vendors = [
            {
                "vendor_name": "ArcelorMittal",
                "price_tolerance_percent": 5.0,
                "contact_email": "accounts@arcelormittal.com"
            },
            {
                "vendor_name": "TechCorp Manufacturing",
                "price_tolerance_percent": 3.0,
                "contact_email": "billing@techcorp.com"
            },
            {
                "vendor_name": "Industrial Solutions LLC",
                "price_tolerance_percent": 7.5,
                "contact_email": "invoices@industrialsolutions.com"
            },
            {
                "vendor_name": "Safety First Industries",
                "price_tolerance_percent": 2.0,
                "contact_email": "finance@safetyfirst.com"
            },
            {
                "vendor_name": "ElectricWorks Corp",
                "price_tolerance_percent": 4.0,
                "contact_email": "accounting@electricworks.com"
            }
        ]
        
        for vendor_data in sample_vendors:
            vendor_setting = models.VendorSetting(**vendor_data)
            db.add(vendor_setting)
        
        db.commit()
        print(f"✅ Created {len(sample_vendors)} vendor settings.")
        
    except Exception as e:
        print(f"❌ Error creating vendor settings: {e}")
        db.rollback()
    finally:
        db.close()

def create_sample_automation_rules():
    """Create sample automation rules."""
    print("🤖 Creating sample automation rules...")
    db = SessionLocal()
    
    try:
        # Check if automation rules already exist
        existing_count = db.query(models.AutomationRule).count()
        if existing_count > 0:
            print(f"⚠️ Found {existing_count} existing automation rules. Skipping creation.")
            return
        
        sample_rules = [
            {
                "rule_name": "Auto-approve small invoices",
                "vendor_name": None,
                "conditions": {"field": "grand_total", "operator": "<", "value": 500},
                "action": "approve",
                "is_active": 1,
                "source": "user"
            },
            {
                "rule_name": "Flag large invoices for review",
                "vendor_name": None,
                "conditions": {"field": "grand_total", "operator": ">", "value": 10000},
                "action": "flag_for_audit",
                "is_active": 1,
                "source": "user"
            },
            {
                "rule_name": "Auto-approve ArcelorMittal invoices under $2000",
                "vendor_name": "ArcelorMittal",
                "conditions": {"field": "grand_total", "operator": "<", "value": 2000},
                "action": "approve",
                "is_active": 1,
                "source": "user"
            },
            {
                "rule_name": "Require review for missing PO",
                "vendor_name": None,
                "conditions": {"field": "po_number", "operator": "is_null", "value": None},
                "action": "reject",
                "is_active": 1,
                "source": "user"
            },
            {
                "rule_name": "Fast-track safety equipment",
                "vendor_name": "Safety First Industries",
                "conditions": {"field": "vendor_name", "operator": "equals", "value": "Safety First Industries"},
                "action": "approve",
                "is_active": 1,
                "source": "user"
            }
        ]
        
        for rule_data in sample_rules:
            automation_rule = models.AutomationRule(**rule_data)
            db.add(automation_rule)
        
        db.commit()
        print(f"✅ Created {len(sample_rules)} automation rules.")
        
    except Exception as e:
        print(f"❌ Error creating automation rules: {e}")
        db.rollback()
    finally:
        db.close()

def main():
    """Initialize all sample configuration data."""
    print("🚀 INITIALIZING SAMPLE CONFIGURATION DATA")
    print("=" * 50)
    
    create_sample_vendor_settings()
    create_sample_automation_rules()
    
    print("=" * 50)
    print("✅ CONFIGURATION DATA INITIALIZATION COMPLETE!")
    print("\n💡 You can now:")
    print("1. Start the backend: python run.py")
    print("2. Start the frontend: streamlit run streamlit_app.py")
    print("3. Navigate to the System Configuration page")
    print("4. View and edit the sample vendor settings and automation rules")

if __name__ == "__main__":
    main() 