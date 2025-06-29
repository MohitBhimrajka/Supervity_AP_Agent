# src/app/api/endpoints/dashboard.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, case, desc, text, cast, Float
from datetime import datetime, date, timedelta
from typing import List, Dict, Any
from collections import Counter

from app.api.dependencies import get_db
from app.db import models, schemas
from app.config import (
    AGENT_COST_PER_INVOICE,
    INFRA_COST_MONTHLY,
    AVG_MANUAL_HANDLING_TIME_HOURS,
    AVG_AP_CLERK_HOURLY_WAGE,
)

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

    # --- MODIFIED: Average Exception Handling Time (in hours) ---
    # Use new tracking field if available, otherwise calculate from audit logs and timestamps
    avg_handling_time_minutes = db.query(
        func.avg(models.Invoice.handling_time_minutes)
    ).filter(
        models.Invoice.handling_time_minutes.isnot(None)
    ).scalar()
    
    # Fallback calculation if no tracked handling times exist
    if avg_handling_time_minutes is None:
        # Get invoices that left needs_review status from audit logs
        processed_handling_times = []
        
        # Find audit logs for invoices leaving needs_review
        exit_review_logs = db.query(models.AuditLog).filter(
            models.AuditLog.action == 'Status Changed',
            models.AuditLog.details.like('%"from": "needs_review"%')
        ).all()
        
        for log in exit_review_logs:
            invoice = db.query(models.Invoice).filter(models.Invoice.invoice_id == log.entity_id).first()
            if invoice:
                # Estimate handling time as time from updated_at to log timestamp
                try:
                    from datetime import datetime
                    if isinstance(log.timestamp, str):
                        log_time = datetime.fromisoformat(log.timestamp.replace('Z', '+00:00'))
                    else:
                        log_time = log.timestamp
                    
                    if isinstance(invoice.updated_at, str):
                        updated_time = datetime.fromisoformat(invoice.updated_at.replace('Z', '+00:00'))
                    else:
                        updated_time = invoice.updated_at
                    
                    handling_time_minutes = (log_time - updated_time).total_seconds() / 60
                    if handling_time_minutes > 0:
                        processed_handling_times.append(handling_time_minutes)
                except Exception:
                    continue
        
        # Also include current invoices in review (time since last update)
        current_review_invoices = db.query(models.Invoice).filter(
            models.Invoice.status == models.DocumentStatus.needs_review
        ).all()
        
        for invoice in current_review_invoices:
            try:
                from datetime import datetime, timezone
                now = datetime.now(timezone.utc)
                if isinstance(invoice.updated_at, str):
                    updated_time = datetime.fromisoformat(invoice.updated_at.replace('Z', '+00:00'))
                else:
                    updated_time = invoice.updated_at
                    if updated_time.tzinfo is None:
                        updated_time = updated_time.replace(tzinfo=timezone.utc)
                
                current_handling_time_minutes = (now - updated_time).total_seconds() / 60
                if current_handling_time_minutes > 0:
                    processed_handling_times.append(current_handling_time_minutes)
            except Exception:
                continue
        
        # Calculate average from fallback data
        if processed_handling_times:
            avg_handling_time_minutes = sum(processed_handling_times) / len(processed_handling_times)


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
            # This key is renamed for clarity on the frontend
            "avg_exception_handling_time_hours": round(avg_handling_time_minutes / 60, 1) if avg_handling_time_minutes is not None else 0,
            "total_processed_invoices": total_processed_invoices,
            "invoices_in_review_queue": db.query(models.Invoice).filter(models.Invoice.status == models.DocumentStatus.needs_review).count(),
        },
        "vendor_performance": {
            "top_vendors_by_exception_rate": top_vendors_by_exception,
            # Placeholder for another valuable metric
            "on_time_payment_rate": "Not Implemented"
        }
    }

@router.get("/exception-summary", response_model=List[schemas.ExceptionSummaryItem], summary="Get Exception Wise Summary")
def get_exception_summary(db: Session = Depends(get_db)):
    """
    Provides a summary of different exception types for invoices needing review.
    """
    invoices_in_review = db.query(models.Invoice).filter(
        models.Invoice.status == models.DocumentStatus.needs_review,
        models.Invoice.match_trace.isnot(None)
    ).all()
    
    exception_counts = Counter()
    
    for inv in invoices_in_review:
        exceptions_in_invoice = set()
        if not inv.match_trace:
            continue
        for step in inv.match_trace:
            if step.get("status") == "FAIL":
                step_name = step.get("step", "Unknown").replace("'", "").replace("Item ", "").strip()
                normalized_name = "".join(word.capitalize() for word in step_name.split())
                exceptions_in_invoice.add(normalized_name)
        
        for exc_type in exceptions_in_invoice:
            exception_counts[exc_type] += 1
    
    summary_list = [
        {"name": name, "count": count} 
        for name, count in exception_counts.most_common()
    ]
    return summary_list

@router.get("/cost-roi", response_model=schemas.CostRoiMetrics, summary="Get Cost and ROI Metrics")
def get_cost_roi_metrics(db: Session = Depends(get_db)):
    """
    Calculates and returns key cost and return-on-investment metrics.
    """
    # Investment Calculation
    processed_invoice_count = db.query(models.Invoice).filter(
        models.Invoice.status.in_([
            models.DocumentStatus.approved_for_payment, 
            models.DocumentStatus.paid, 
            models.DocumentStatus.rejected
        ])
    ).count()
    
    agent_expense = processed_invoice_count * AGENT_COST_PER_INVOICE
    
    # Return Calculation
    # Touchless count
    invoices_needing_review_ids = db.query(models.Invoice.id).filter(
        models.Invoice.status == models.DocumentStatus.needs_review
    ).subquery()
    touchless_invoices_count = db.query(models.Invoice).filter(
        models.Invoice.status.in_([models.DocumentStatus.approved_for_payment, models.DocumentStatus.paid]),
        models.Invoice.id.notin_(invoices_needing_review_ids)
    ).count()
    
    time_saved_value = (
        touchless_invoices_count * 
        AVG_MANUAL_HANDLING_TIME_HOURS * 
        AVG_AP_CLERK_HOURLY_WAGE
    )
    
    discounts_captured = db.query(func.sum(models.Invoice.discount_amount)).filter(
        models.Invoice.status == models.DocumentStatus.paid,
        models.Invoice.paid_date <= models.Invoice.discount_due_date,
        models.Invoice.discount_amount.isnot(None)
    ).scalar() or 0.0
    
    total_return = time_saved_value + discounts_captured
    ai_roi = total_return - agent_expense
    
    return {
        "agent_expense": agent_expense,
        "infra_cost_monthly": INFRA_COST_MONTHLY,
        "total_investment_todate": agent_expense,
        "time_saved_value": time_saved_value,
        "discounts_captured_value": discounts_captured,
        "total_return_todate": total_return,
        "ai_roi_todate": ai_roi,
        "processed_invoice_count": processed_invoice_count,
    } 