# src/app/api/endpoints/configuration.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, cast, Float, case
from typing import List, Optional
from pydantic import BaseModel

from app.api.dependencies import get_db
from app.db import models, schemas

router = APIRouter()

# --- NEW SCHEMA for Vendor Performance ---
class VendorPerformanceSummary(schemas.VendorSetting):
    total_invoices: int
    exception_rate: float
    avg_payment_time_days: Optional[float]

# --- NEW ENDPOINT for Vendor Performance ---
@router.get("/vendor-performance-summary", response_model=List[VendorPerformanceSummary])
def get_vendor_performance_summary(db: Session = Depends(get_db)):
    """
    Retrieves all vendor settings and enriches them with performance KPIs.
    """
    settings = db.query(models.VendorSetting).all()
    vendor_names = [s.vendor_name for s in settings]
    
    # Pre-calculate stats for all vendors with settings
    invoice_stats = db.query(
        models.Invoice.vendor_name,
        func.count(models.Invoice.id).label('total_invoices'),
        (cast(func.sum(case((models.Invoice.status == models.DocumentStatus.needs_review, 1), else_=0)), Float) / cast(func.count(models.Invoice.id), Float) * 100).label('exception_rate'),
        func.avg(func.julianday(models.Invoice.paid_date) - func.julianday(models.Invoice.invoice_date)).label('avg_payment_days')
    ).filter(models.Invoice.vendor_name.in_(vendor_names)).group_by(models.Invoice.vendor_name).all()

    stats_map = {row.vendor_name: row for row in invoice_stats}
    
    results = []
    for setting in settings:
        stats = stats_map.get(setting.vendor_name)
        summary = VendorPerformanceSummary(
            **setting.__dict__,
            total_invoices=stats.total_invoices if stats else 0,
            exception_rate=round(stats.exception_rate, 1) if stats and stats.exception_rate is not None else 0.0,
            avg_payment_time_days=round(stats.avg_payment_days, 1) if stats and stats.avg_payment_days is not None else None
        )
        results.append(summary)
        
    return sorted(results, key=lambda x: x.exception_rate, reverse=True)


# --- Vendor Settings Endpoints (Full CRUD) ---
@router.get("/vendor-settings", response_model=List[schemas.VendorSetting])
def get_all_vendor_settings(db: Session = Depends(get_db)):
    """Retrieves all vendor-specific settings."""
    return db.query(models.VendorSetting).order_by(models.VendorSetting.vendor_name).all()

@router.post("/vendor-settings", response_model=schemas.VendorSetting, status_code=status.HTTP_201_CREATED)
def create_vendor_setting(setting_data: schemas.VendorSettingCreate, db: Session = Depends(get_db)):
    """Creates a new vendor-specific setting."""
    new_setting = models.VendorSetting(**setting_data.model_dump())
    db.add(new_setting)
    db.commit()
    db.refresh(new_setting)
    return new_setting

@router.put("/vendor-settings/{setting_id}", response_model=schemas.VendorSetting)
def update_single_vendor_setting(setting_id: int, setting_data: schemas.VendorSettingCreate, db: Session = Depends(get_db)):
    """Updates a single vendor setting."""
    setting = db.query(models.VendorSetting).filter(models.VendorSetting.id == setting_id).first()
    if not setting:
        raise HTTPException(status_code=404, detail="Vendor setting not found")
    update_data = setting_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(setting, key, value)
    db.commit()
    db.refresh(setting)
    return setting

@router.delete("/vendor-settings/{setting_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vendor_setting(setting_id: int, db: Session = Depends(get_db)):
    """Deletes a vendor setting."""
    setting = db.query(models.VendorSetting).filter(models.VendorSetting.id == setting_id).first()
    if not setting:
        raise HTTPException(status_code=404, detail="Vendor setting not found")
    db.delete(setting)
    db.commit()
    return

# --- Automation Rules Endpoints (Full CRUD) ---
@router.get("/automation-rules", response_model=List[schemas.AutomationRule])
def get_all_automation_rules(db: Session = Depends(get_db)):
    """Retrieves all automation rules."""
    return db.query(models.AutomationRule).order_by(models.AutomationRule.id).all()

@router.post("/automation-rules", response_model=schemas.AutomationRule, status_code=status.HTTP_201_CREATED)
def create_new_automation_rule(rule_data: schemas.AutomationRuleCreate, db: Session = Depends(get_db)):
    """Creates a new automation rule."""
    new_rule = models.AutomationRule(**rule_data.model_dump())
    db.add(new_rule)
    db.commit()
    db.refresh(new_rule)
    return new_rule

@router.put("/automation-rules/{rule_id}", response_model=schemas.AutomationRule)
def update_automation_rule(rule_id: int, rule_data: schemas.AutomationRuleCreate, db: Session = Depends(get_db)):
    """Updates an automation rule."""
    rule = db.query(models.AutomationRule).filter(models.AutomationRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Automation rule not found")
        
    update_data = rule_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(rule, key, value)
        
    db.commit()
    db.refresh(rule)
    return rule

@router.delete("/automation-rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_automation_rule(rule_id: int, db: Session = Depends(get_db)):
    """Deletes an automation rule."""
    rule = db.query(models.AutomationRule).filter(models.AutomationRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Automation rule not found")
        
    db.delete(rule)
    db.commit()
    return 