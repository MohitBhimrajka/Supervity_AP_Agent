# src/app/api/endpoints/dashboard.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, case, desc, text, cast, Float
from datetime import datetime, date, timedelta

from app.api.dependencies import get_db
from app.db import models

router = APIRouter()

@router.get("/summary", summary="Get Basic Summary")
def get_dashboard_summary(db: Session = Depends(get_db)):
    """
    Provides high-level KPI numbers for the main dashboard view.
    """
    total_value_exceptions = db.query(func.sum(models.Invoice.grand_total)).filter(
        models.Invoice.status == models.DocumentStatus.needs_review,
        models.Invoice.grand_total.isnot(None)
    ).scalar() or 0.0

    total_value_pending = db.query(func.sum(models.Invoice.grand_total)).filter(
        models.Invoice.status == models.DocumentStatus.pending_match,
        models.Invoice.grand_total.isnot(None)
    ).scalar() or 0.0

    summary = {
        "total_invoices": db.query(models.Invoice).count(),
        "requires_review": db.query(models.Invoice).filter(models.Invoice.status == models.DocumentStatus.needs_review).count(),
        "approved_for_payment": db.query(models.Invoice).filter(models.Invoice.status == models.DocumentStatus.approved_for_payment).count(),
        "pending_match": db.query(models.Invoice).filter(models.Invoice.status == models.DocumentStatus.pending_match).count(),
        "total_pos": db.query(models.PurchaseOrder).count(),
        "total_grns": db.query(models.GoodsReceiptNote).count(),
        "total_value_exceptions": total_value_exceptions,
        "total_value_pending": total_value_pending,
    }
    return summary

@router.get("/kpis", summary="Get Advanced Business KPIs")
def get_advanced_kpis(db: Session = Depends(get_db)):
    """
    Provides a comprehensive set of Key Performance Indicators for business users,
    including efficiency, financial, and vendor performance metrics.
    """
    today = date.today()

    # --- 1. FINANCIAL OPTIMIZATION KPIS ---
    discounts_captured = db.query(func.sum(models.Invoice.discount_amount)).filter(
        models.Invoice.status == models.DocumentStatus.paid,
        models.Invoice.paid_date <= models.Invoice.discount_due_date,
        models.Invoice.discount_amount.isnot(None)
    ).scalar() or 0.0

    discounts_missed = db.query(func.sum(models.Invoice.discount_amount)).filter(
        models.Invoice.status == models.DocumentStatus.paid,
        models.Invoice.paid_date > models.Invoice.discount_due_date,
        models.Invoice.discount_amount.isnot(None)
    ).scalar() or 0.0
    
    discounts_available = db.query(func.sum(models.Invoice.discount_amount)).filter(
        models.Invoice.status == models.DocumentStatus.approved_for_payment,
        models.Invoice.discount_due_date >= today,
        models.Invoice.discount_amount.isnot(None)
    ).scalar() or 0.0

    # Days Payable Outstanding (DPO) - A more accurate calculation
    # (Sum of (Ending AP * Number of Days in Period)) / Total Credit Purchases
    # A simplified proxy: Average time from invoice date to paid date.
    avg_payment_time_days = db.query(
        func.avg(func.julianday(models.Invoice.paid_date) - func.julianday(models.Invoice.invoice_date))
    ).filter(models.Invoice.status == models.DocumentStatus.paid).scalar()

    # --- 2. OPERATIONAL EFFICIENCY KPIS ---
    
    # Total invoices that have been fully processed (approved, paid, or rejected)
    total_processed_invoices = db.query(models.Invoice).filter(
        models.Invoice.status.in_([
            models.DocumentStatus.approved_for_payment, 
            models.DocumentStatus.paid, 
            models.DocumentStatus.rejected
        ])
    ).count()

    # Touchless Invoice Rate: % of invoices that went from pending_match -> approved/paid without ever needing review.
    invoices_needing_review_ids = db.query(models.Invoice.id).filter(
        models.Invoice.status == models.DocumentStatus.needs_review
    ).subquery()
    
    touchless_invoices_count = db.query(models.Invoice).filter(
        models.Invoice.status.in_([
            models.DocumentStatus.approved_for_payment, 
            models.DocumentStatus.paid
        ]),
        models.Invoice.id.notin_(invoices_needing_review_ids)
    ).count()
    
    touchless_rate_percent = (touchless_invoices_count / total_processed_invoices * 100) if total_processed_invoices > 0 else 100

    # Average Exception Handling Time (in hours)
    # Using AuditLog to find time from entering 'needs_review' to leaving it.
    # This is a complex query, simplified here. A real implementation might use a dedicated analytics view.
    # For now, we calculate avg time an invoice has *been* in 'needs_review'
    avg_exception_age_hours = db.query(
        func.avg(func.julianday('now') - func.julianday(models.Invoice.updated_at)) * 24
    ).filter(models.Invoice.status == models.DocumentStatus.needs_review).scalar()


    # --- 3. VENDOR PERFORMANCE KPIS ---

    # Vendor Exception Rate: Which vendors cause the most issues?
    vendor_exception_query = db.query(
        models.Invoice.vendor_name,
        (cast(func.sum(case((models.Invoice.status == models.DocumentStatus.needs_review, 1), else_=0)), Float) / func.count(models.Invoice.id) * 100).label('exception_rate')
    ).group_by(models.Invoice.vendor_name).order_by(desc('exception_rate')).limit(5).all()

    top_vendors_by_exception = {
        vendor: f"{rate:.2f}%" for vendor, rate in vendor_exception_query if vendor
    }


    return {
        "financial_optimization": {
            "discounts_captured": f"${discounts_captured:,.2f}",
            "discounts_missed": f"${discounts_missed:,.2f}",
            "discounts_pending": f"${discounts_available:,.2f}",
            "days_payable_outstanding_proxy": round(avg_payment_time_days, 1) if avg_payment_time_days else 0
        },
        "operational_efficiency": {
            "touchless_invoice_rate_percent": round(touchless_rate_percent, 2),
            "avg_exception_handling_time_hours": round(avg_exception_age_hours, 1) if avg_exception_age_hours else 0,
            "total_processed_invoices": total_processed_invoices,
            "invoices_in_review_queue": db.query(models.Invoice).filter(models.Invoice.status == models.DocumentStatus.needs_review).count(),
        },
        "vendor_performance": {
            "top_vendors_by_exception_rate": top_vendors_by_exception,
            # Placeholder for another valuable metric
            "on_time_payment_rate": "Not Implemented"
        }
    } 