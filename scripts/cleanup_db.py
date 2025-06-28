#!/usr/bin/env python3
"""
Database cleanup script to remove all data and start fresh.
"""

import os
import sys
from sqlalchemy import text

# Add both the project root and src directory to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
src_dir = os.path.join(project_root, 'src')
sys.path.insert(0, project_root)
sys.path.insert(0, src_dir)

# CORRECTED IMPORTS
from app.db.session import SessionLocal, engine
from app.db import models

def cleanup_database():
    """Remove all data from the database."""
    print("🧹 Cleaning up database...")
    db = SessionLocal()
    try:
        # Delete all data from tables in correct order (respecting foreign keys)
        print("Deleting data from tables...")
        db.execute(text("DELETE FROM notifications"))      # New table
        db.execute(text("DELETE FROM learned_heuristics")) # New table
        db.execute(text("DELETE FROM audit_logs"))
        db.execute(text("DELETE FROM invoices"))
        db.execute(text("DELETE FROM goods_receipt_notes"))
        db.execute(text("DELETE FROM purchase_orders"))
        db.execute(text("DELETE FROM jobs"))
        db.execute(text("DELETE FROM vendor_settings")) 
        db.execute(text("DELETE FROM automation_rules")) # New table
        
        db.commit()
        print("✅ Database cleaned successfully!")
        
        # Show counts
        invoice_count = db.query(models.Invoice).count()
        grn_count = db.query(models.GoodsReceiptNote).count()
        po_count = db.query(models.PurchaseOrder).count()
        job_count = db.query(models.Job).count()
        
        print(f"📊 Current counts: Jobs: {job_count}, POs: {po_count}, GRNs: {grn_count}, Invoices: {invoice_count}")
        
    except Exception as e:
        print(f"❌ Error cleaning database: {e}")
        db.rollback()
    finally:
        db.close()

def reset_database():
    """Drop and recreate all tables."""
    print("🔄 Resetting database schema...")
    try:
        # This will drop all tables including the new ones
        models.Base.metadata.drop_all(bind=engine)
        print("✅ Dropped all tables.")
        
        # This will create all tables including the new ones
        models.Base.metadata.create_all(bind=engine)
        print("✅ Recreated all tables.")
        
    except Exception as e:
        print(f"❌ Error resetting database: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--reset":
        print("Running full database reset (drop and recreate tables)...")
        reset_database()
    else:
        print("Running database cleanup (deleting all data)...")
        cleanup_database()
    
    print("🚀 Database is ready for processing!") 