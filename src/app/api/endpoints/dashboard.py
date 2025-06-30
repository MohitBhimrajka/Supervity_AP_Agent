# src/app/api/endpoints/dashboard.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, Query as SQLQuery
from sqlalchemy import func, case, desc, cast, Float
from datetime import datetime, date, timedelta
from typing import Optional

from app.api.dependencies import get_db
from app.db import models

router = APIRouter()

# --- HELPER FUNCTION TO APPLY DATE FILTERS ---
def _get_date_filtered_query(db: Session, model, start_date: Optional[date] = None, end_date: Optional[date] = None) -> SQLQuery:
    """Applies a date filter to a query based on the 'created_at' field."""
    query = db.query(model)
    if start_date:
        query = query.filter(model.created_at >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        query = query.filter(model.created_at <= datetime.combine(end_date, datetime.max.time()))
    return query

# --- UPDATED ENDPOINTS ---

@router.get("/summary", summary="Get Basic Summary")
def get_dashboard_summary(
    db: Session = Depends(get_db),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None)
):
    """Provides high-level KPI numbers for the main dashboard view, filterable by date."""
    base_query = _get_date_filtered_query(db, models.Invoice, start_date, end_date)

    total_value_exceptions = base_query.filter(
        models.Invoice.status == models.DocumentStatus.needs_review,
        models.Invoice.grand_total.isnot(None)
    ).with_entities(func.sum(models.Invoice.grand_total)).scalar() or 0.0

    # Get kpis for the same period to calculate touchless count
    kpis = get_advanced_kpis(db, start_date, end_date)
    op_eff = kpis.get("operational_efficiency", {})
    touchless_rate = op_eff.get("touchless_invoice_rate_percent", 0)
    total_processed = op_eff.get("total_processed_invoices", 0)
    auto_approved_count = round((touchless_rate / 100) * total_processed)

    summary = {
        "total_invoices": base_query.count(),
        "requires_review": base_query.filter(models.Invoice.status == models.DocumentStatus.needs_review).count(),
        "auto_approved": auto_approved_count,
        "pending_match": base_query.filter(models.Invoice.status == models.DocumentStatus.pending_match).count(),
        # POs and GRNs are not date-filtered as they are master data
        "total_pos": db.query(models.PurchaseOrder).count(),
        "total_grns": db.query(models.GoodsReceiptNote).count(),
        "total_value_exceptions": total_value_exceptions,
    }
    return summary

@router.get("/kpis", summary="Get Advanced Business KPIs")
def get_advanced_kpis(
    db: Session = Depends(get_db),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None)
):
    """Provides a comprehensive set of Key Performance Indicators, filterable by date."""
    base_query = _get_date_filtered_query(db, models.Invoice, start_date, end_date)

    # --- Current Period Calculations ---
    discounts_captured = base_query.filter(models.Invoice.status == models.DocumentStatus.paid, models.Invoice.paid_date <= models.Invoice.discount_due_date, models.Invoice.discount_amount.isnot(None)).with_entities(func.sum(models.Invoice.discount_amount)).scalar() or 0.0
    
    total_processed_invoices = base_query.filter(models.Invoice.status.in_([models.DocumentStatus.approved_for_payment, models.DocumentStatus.paid, models.DocumentStatus.needs_review])).count()
    invoices_in_review = base_query.filter(models.Invoice.status == models.DocumentStatus.needs_review).count()
    touchless_invoices = total_processed_invoices - invoices_in_review
    touchless_rate_percent = (touchless_invoices / total_processed_invoices * 100) if total_processed_invoices > 0 else 0.0
    
    avg_exception_age_hours_result = base_query.filter(models.Invoice.status == models.DocumentStatus.needs_review).with_entities(func.avg(func.julianday('now') - func.julianday(models.Invoice.updated_at)) * 24).scalar()
    avg_exception_age_hours = avg_exception_age_hours_result or 0

    # --- Previous Period Calculations for Trend ---
    prev_start_date, prev_end_date = None, None
    if start_date and end_date:
        duration = end_date - start_date
        prev_end_date = start_date - timedelta(days=1)
        prev_start_date = prev_end_date - duration
        
        prev_base_query = _get_date_filtered_query(db, models.Invoice, prev_start_date, prev_end_date)
        prev_total_processed = prev_base_query.filter(models.Invoice.status.in_([models.DocumentStatus.approved_for_payment, models.DocumentStatus.paid, models.DocumentStatus.needs_review])).count()
        prev_in_review = prev_base_query.filter(models.Invoice.status == models.DocumentStatus.needs_review).count()
        prev_touchless = prev_total_processed - prev_in_review
        prev_touchless_rate = (prev_touchless / prev_total_processed * 100) if prev_total_processed > 0 else 0.0
    else:
        prev_touchless_rate = 0 # No trend if no date range

    # --- Vendor Performance (always on the selected period) ---
    vendor_exception_query = base_query.with_entities(models.Invoice.vendor_name, (cast(func.sum(case((models.Invoice.status == models.DocumentStatus.needs_review, 1), else_=0)), Float) / cast(func.count(models.Invoice.id), Float) * 100).label('exception_rate')).group_by(models.Invoice.vendor_name).order_by(desc('exception_rate')).limit(5).all()
    top_vendors_by_exception = { vendor: f"{rate:.1f}%" for vendor, rate in vendor_exception_query if vendor and rate is not None }

    return {
        "financial_optimization": { "discounts_captured": f"${discounts_captured:,.2f}" },
        "operational_efficiency": {
            "touchless_invoice_rate_percent": round(touchless_rate_percent, 1),
            "touchless_rate_change": round(touchless_rate_percent - prev_touchless_rate, 1),
            "avg_exception_handling_time_hours": round(avg_exception_age_hours, 1),
            "total_processed_invoices": total_processed_invoices,
            "invoices_in_review_queue": invoices_in_review,
        },
        "vendor_performance": { "top_vendors_by_exception_rate": top_vendors_by_exception }
    }

@router.get("/exceptions", summary="Get Exception Summary")
def get_exception_summary(
    db: Session = Depends(get_db),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None)
):
    """Provides a summary of invoice exceptions by category for a chart, filterable by date."""
    base_query = _get_date_filtered_query(db, models.Invoice, start_date, end_date)
    results = base_query.filter(
        models.Invoice.status == models.DocumentStatus.needs_review,
        models.Invoice.review_category.isnot(None)
    ).with_entities(
        models.Invoice.review_category,
        func.count(models.Invoice.id).label('count')
    ).group_by(models.Invoice.review_category).all()
    
    return [{"name": row[0].replace('_', ' ').title(), "count": row[1]} for row in results]

@router.get("/cost-roi", summary="Get Cost and ROI Metrics")
def get_cost_roi_metrics(
    db: Session = Depends(get_db),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None)
):
    """Calculates estimated cost savings and ROI for the AP automation, filterable by date."""
    base_query = _get_date_filtered_query(db, models.Invoice, start_date, end_date)
    kpis = get_advanced_kpis(db, start_date, end_date) # Reuse KPI logic for consistency
    
    COST_PER_INVOICE = 0.05
    HOURLY_RATE_AP_CLERK = 40.00
    MINUTES_SAVED_PER_TOUCHLESS_INVOICE = 5
    
    total_processed = kpis["operational_efficiency"]["total_processed_invoices"]
    touchless_count = total_processed - kpis["operational_efficiency"]["invoices_in_review_queue"]
    
    agent_expense = total_processed * COST_PER_INVOICE
    time_saved_value = (touchless_count * MINUTES_SAVED_PER_TOUCHLESS_INVOICE / 60) * HOURLY_RATE_AP_CLERK
    discounts_captured_value = float(kpis["financial_optimization"]["discounts_captured"].replace('$', '').replace(',', ''))
    
    total_return = time_saved_value + discounts_captured_value
    
    return { "total_return_for_period": total_return, "total_cost_for_period": agent_expense } 