# src/app/api/endpoints/configuration.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.api.dependencies import get_db
from app.db import models, schemas

router = APIRouter()

# --- Vendor Settings Endpoints ---

@router.get("/vendor-settings", response_model=List[schemas.VendorSetting])
def get_all_vendor_settings(db: Session = Depends(get_db)):
    """Retrieves all vendor-specific settings."""
    return db.query(models.VendorSetting).all()

@router.put("/vendor-settings", response_model=List[schemas.VendorSetting])
def update_vendor_settings(settings_list: List[schemas.VendorSettingUpdate], db: Session = Depends(get_db)):
    """Updates a list of vendor settings. Used by the data editor."""
    updated_settings = []
    for setting_data in settings_list:
        setting = db.query(models.VendorSetting).filter_by(id=setting_data.id).first()
        if not setting:
            # Optionally, you could create a new one, but for an editor, we expect it to exist.
            continue
        
        update_data = setting_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(setting, key, value)
        
        db.add(setting)
        updated_settings.append(setting)
    
    db.commit()
    return updated_settings

# --- Automation Rules Endpoints ---

@router.get("/automation-rules", response_model=List[schemas.AutomationRule])
def get_all_automation_rules(db: Session = Depends(get_db)):
    """Retrieves all automation rules."""
    return db.query(models.AutomationRule).order_by(models.AutomationRule.id).all()

@router.post("/automation-rules", response_model=schemas.AutomationRule)
def create_new_automation_rule(rule_data: schemas.AutomationRuleCreate, db: Session = Depends(get_db)):
    """Creates a new automation rule."""
    new_rule = models.AutomationRule(**rule_data.model_dump())
    db.add(new_rule)
    db.commit()
    db.refresh(new_rule)
    return new_rule 