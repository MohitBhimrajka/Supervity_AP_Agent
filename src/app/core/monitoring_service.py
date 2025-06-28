from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.db import models
from app.db.session import SessionLocal

def _create_notification_if_not_exists(db: Session, type: str, message: str, entity_id: str, entity_type: str, action: dict = None):
    """Prevents creating duplicate notifications."""
    existing = db.query(models.Notification).filter_by(
        type=type,
        related_entity_id=entity_id,
        is_read=0
    ).first()
    
    if not existing:
        new_notif = models.Notification(
            type=type,
            message=message,
            related_entity_id=entity_id,
            related_entity_type=entity_type,
            proposed_action=action
        )
        db.add(new_notif)
        print(f"💡 PROACTIVE: Generated new '{type}' notification for {entity_type} {entity_id}.")

def check_for_automation_suggestions(db: Session):
    """
    Scans high-confidence learned heuristics and suggests promoting them to
    formal automation rules.
    """
    # Find heuristics with high confidence that don't already have a corresponding rule
    high_confidence_heuristics = db.query(models.LearnedHeuristic).filter(
        models.LearnedHeuristic.confidence_score >= 0.9
    ).all()
    
    for heuristic in high_confidence_heuristics:
        # Check if an automation rule for this exact case already exists
        existing_rule = db.query(models.AutomationRule).filter_by(
            vendor_name=heuristic.vendor_name,
            conditions=heuristic.learned_condition,
            action=heuristic.resolution_action
        ).first()

        if not existing_rule:
            message = f"You often approve '{heuristic.exception_type}' for '{heuristic.vendor_name}' under certain conditions. Would you like to automate this?"
            action = {
                "tool_name": "create_automation_rule",
                "args": {
                    "rule_name": f"Auto-approve {heuristic.exception_type} for {heuristic.vendor_name}",
                    "vendor_name": heuristic.vendor_name,
                    "condition_json": str(heuristic.learned_condition).replace("'", '"'),
                    "action": "approve" # Hard-coded for now
                }
            }
            _create_notification_if_not_exists(db, "AutomationSuggestion", message, heuristic.vendor_name, "Vendor", action)


def check_for_financial_optimizations(db: Session):
    """
    Scans for invoices with approaching early payment discounts.
    """
    deadline = datetime.now().date() + timedelta(days=3)
    
    invoices_with_discounts = db.query(models.Invoice).filter(
        models.Invoice.status == models.DocumentStatus.approved_for_payment,
        models.Invoice.discount_due_date.isnot(None),
        models.Invoice.discount_due_date <= deadline,
        models.Invoice.discount_due_date >= datetime.now().date()
    ).all()

    for inv in invoices_with_discounts:
        message = f"Early payment discount of ${inv.discount_amount or 0:,.2f} for Invoice {inv.invoice_id} is expiring on {inv.discount_due_date}. Pay now to capture it."
        _create_notification_if_not_exists(db, "Optimization", message, inv.invoice_id, "Invoice")

def run_monitoring_cycle():
    """
    The main entry point for the proactive engine's check-up.
    This function is called periodically by the background scheduler.
    """
    print("--- 🧠 Running Proactive Monitoring Cycle ---")
    db = SessionLocal()
    try:
        check_for_automation_suggestions(db)
        check_for_financial_optimizations(db)
        # Placeholder for more checks, like fraud detection
        db.commit()
    except Exception as e:
        print(f"❌ Error during monitoring cycle: {e}")
        db.rollback()
    finally:
        db.close()
    print("--- ✅ Monitoring Cycle Complete ---") 