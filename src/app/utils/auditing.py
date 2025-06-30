from sqlalchemy.orm import Session
from typing import Optional, Dict, Any

from app.db import models

def log_audit_event(
    db: Session,
    invoice_db_id: int,
    user: str,
    action: str,
    summary: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    commit: bool = False
):
    """Creates and adds an audit log entry to the database session."""
    invoice_id_str = db.query(models.Invoice.invoice_id).filter(models.Invoice.id == invoice_db_id).scalar()
    if not invoice_id_str:
        print(f"Warning: Audit log for non-existent invoice DB ID {invoice_db_id}")
        return

    audit_log = models.AuditLog(
        entity_type='Invoice',
        entity_id=invoice_id_str,
        invoice_db_id=invoice_db_id,
        user=user,
        action=action,
        summary=summary,
        details=details or {}
    )
    db.add(audit_log)

    if commit:
        db.commit() 