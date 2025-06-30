# src/app/modules/copilot/tools.py
import json
import os
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from google.genai import types as genai_types
from thefuzz import fuzz

from app.db import models, schemas
from app.utils import data_formatting
from app.config import settings
from sample_data.pdf_templates import draw_po_pdf

GENERATED_DOCS_DIR = "generated_documents"
os.makedirs(GENERATED_DOCS_DIR, exist_ok=True)


# --- Helper Function ---
def make_json_serializable(data: Any) -> Any:
    """Converts a Python object into a JSON-serializable version."""
    return json.loads(json.dumps(data, default=str))

# --- Tool Definitions and Implementations ---

# --- Analysis & Read-Only Tools ---
get_system_kpis_declaration = genai_types.FunctionDeclaration(
    name="get_system_kpis",
    description="Gets key performance indicators (KPIs) for the entire AP system. This includes strategic metrics like touchless invoice rate, discount capture, average payment times, and vendor exception rates."
)
def get_system_kpis(db: Session) -> Dict[str, Any]:
    from app.api.endpoints.dashboard import get_advanced_kpis
    print("Executing tool: get_system_kpis")
    kpis = get_advanced_kpis(db)
    return make_json_serializable(kpis)

search_invoices_declaration = genai_types.FunctionDeclaration(
    name="search_invoices",
    description="Searches for invoices with specific filters like status, vendor name, or date range.",
    parameters=genai_types.Schema(
        type=genai_types.Type.OBJECT,
        properties={
            "status": genai_types.Schema(type=genai_types.Type.STRING),
            "vendor_name": genai_types.Schema(type=genai_types.Type.STRING),
            "days_ago": genai_types.Schema(type=genai_types.Type.INTEGER)
        }
    )
)
def search_invoices(db: Session, status: Optional[str] = None, vendor_name: Optional[str] = None, days_ago: Optional[int] = None) -> List[Dict[str, Any]]:
    print(f"Executing tool: search_invoices with status={status}, vendor={vendor_name}, days_ago={days_ago}")
    query = db.query(models.Invoice)
    
    if status:
        # --- FIX START ---
        # Sanitize the status string from the LLM to match the enum value format.
        sanitized_status = status.lower().replace(' ', '_')
        try:
            status_enum = models.DocumentStatus(sanitized_status)
            query = query.filter(models.Invoice.status == status_enum)
        except ValueError:
            # If still invalid, return a helpful error.
            valid_statuses = [e.value for e in models.DocumentStatus]
            return [{"error": f"Invalid status value '{status}'. Valid options are: {valid_statuses}"}]
        # --- FIX END ---
    
    if vendor_name:
        query = query.filter(models.Invoice.vendor_name.ilike(f"%{vendor_name}%"))
        
    if days_ago is not None:
        start_date = datetime.now().date() - timedelta(days=days_ago)
        query = query.filter(models.Invoice.invoice_date >= start_date)
        
    results = query.order_by(models.Invoice.invoice_date.desc()).limit(20).all()
    
    if not results:
        return []

    summary_list = [
        {
            "invoice_id": inv.invoice_id,
            "vendor_name": inv.vendor_name,
            "grand_total": inv.grand_total,
            "status": inv.status.value,
            "invoice_date": str(inv.invoice_date)
        }
        for inv in results
    ]
    return make_json_serializable(summary_list)

get_invoice_details_declaration = genai_types.FunctionDeclaration(
    name="get_invoice_details",
    description="Retrieves a complete dossier (including related PO and GRN) for a single invoice ID.",
    parameters=genai_types.Schema(
        type=genai_types.Type.OBJECT,
        properties={
            "invoice_id": genai_types.Schema(type=genai_types.Type.STRING)
        }
    )
)
def get_invoice_details(db: Session, invoice_id: str) -> Dict[str, Any]:
    print(f"Executing tool: get_invoice_details for invoice_id={invoice_id}")
    invoice = db.query(models.Invoice).filter(models.Invoice.invoice_id == invoice_id).first()
    if not invoice: return {"error": f"Invoice with ID '{invoice_id}' not found."}
    dossier = data_formatting.format_full_dossier(invoice, db)
    return make_json_serializable(dossier)


summarize_vendor_issues_declaration = genai_types.FunctionDeclaration(
    name="summarize_vendor_issues",
    description="Analyzes and summarizes the most common problems for a specific vendor based on invoice exceptions.",
    parameters=genai_types.Schema(
        type=genai_types.Type.OBJECT,
        properties={
            "vendor_name": genai_types.Schema(type=genai_types.Type.STRING)
        }
    )
)
def summarize_vendor_issues(db: Session, vendor_name: str) -> Dict[str, Any]:
    print(f"Executing tool: summarize_vendor_issues for vendor={vendor_name}")
    
    # --- MODIFIED SECTION ---
    # Query invoices in review that have a match trace
    invoices_in_review = db.query(models.Invoice).filter(
        models.Invoice.vendor_name.ilike(f"%{vendor_name}%"), 
        models.Invoice.status == models.DocumentStatus.needs_review, 
        models.Invoice.match_trace.isnot(None)
    ).all()
    
    if not invoices_in_review: 
        return {"message": f"No invoices with recorded issues found for vendor '{vendor_name}'."}

    issue_counts: Dict[str, int] = {}
    total_issues = 0
    for inv in invoices_in_review:
        # Iterate through the trace to find failures
        for step in inv.match_trace:
            if step.get("status") == "FAIL":
                # Normalize the step name into an issue type
                issue_type = step.get("step").replace("'", "").replace("Item ", "")
                issue_counts[issue_type] = issue_counts.get(issue_type, 0) + 1
                total_issues += 1
    # --- END MODIFICATION ---

    sorted_issues = sorted(issue_counts.items(), key=lambda item: item[1], reverse=True)
    result = {
        "vendor_name": vendor_name, 
        "total_invoices_with_issues": len(invoices_in_review), 
        "total_exceptions": total_issues, 
        "common_issues": dict(sorted_issues)
    }
    return make_json_serializable(result)


flag_potential_anomalies_declaration = genai_types.FunctionDeclaration(
    name="flag_potential_anomalies",
    description="Scans recent invoices to detect potential anomalies like duplicate payments or unusual spending.",
    parameters=genai_types.Schema(
        type=genai_types.Type.OBJECT,
        properties={
            "days_ago": genai_types.Schema(
                type=genai_types.Type.INTEGER,
                description="How many days back to scan. Defaults to 7."
            )
        }
    )
)
def flag_potential_anomalies(db: Session, days_ago: int = 7) -> Dict[str, Any]:
    print("Executing tool: flag_potential_anomalies")
    start_date = datetime.now() - timedelta(days=days_ago)
    recent_invoices = db.query(models.Invoice).filter(models.Invoice.created_at >= start_date).all()
    anomalies = []
    # Simplified duplicate check
    for i, inv1 in enumerate(recent_invoices):
        for inv2 in recent_invoices[i+1:]:
            if inv1.vendor_name == inv2.vendor_name and inv1.id != inv2.id:
                amount_similarity = fuzz.ratio(str(inv1.grand_total), str(inv2.grand_total))
                if amount_similarity > 95: # Very close amounts
                    anomalies.append({
                        "type": "Potential Duplicate Payment",
                        "message": f"Invoice {inv1.invoice_id} and {inv2.invoice_id} from {inv1.vendor_name} have very similar amounts (${inv1.grand_total} and ${inv2.grand_total}).",
                        "invoices": [inv1.invoice_id, inv2.invoice_id]
                    })
    # Unusual spend check (simplified)
    # A real implementation would use standard deviation over a longer period
    return {"found_anomalies": anomalies if anomalies else "No obvious anomalies found in the last 7 days."}

analyze_spending_by_category_declaration = genai_types.FunctionDeclaration(
    name="analyze_spending_by_category",
    description="Analyzes invoice line items to break down spending by category for a given period.",
    parameters=genai_types.Schema(
        type=genai_types.Type.OBJECT,
        properties={
            "period": genai_types.Schema(
                type=genai_types.Type.STRING,
                description="e.g., 'last month', 'last quarter', 'last 7 days'"
            )
        }
    )
)
def analyze_spending_by_category(db: Session, client: Any, period: str = "last month") -> Dict[str, Any]:
    print(f"Executing tool: analyze_spending_by_category for period: {period}")
    today = datetime.now()
    if "month" in period: start_date = today - relativedelta(months=1)
    elif "quarter" in period: start_date = today - relativedelta(months=3)
    else: start_date = today - relativedelta(days=7)
    
    line_items_text = ""
    paid_invoices = db.query(models.Invoice).filter(models.Invoice.paid_date >= start_date.date()).all()
    for inv in paid_invoices:
        if inv.line_items:
            for item in inv.line_items:
                line_items_text += f"{item.get('description', '')}, cost: {item.get('line_total', 0)}\n"
    
    if not line_items_text:
        return {"error": "No paid invoice line items found for the specified period."}

    prompt = f"""You are a procurement analyst. Based on the following list of purchased items, categorize them into broad spending categories like 'Raw Materials', 'Contractor Services', 'Software & IT', 'Office Supplies', 'Shipping & Logistics', 'Utilities'. Sum up the total for each category. Provide the output as a JSON object.

Items:
{line_items_text[:4000]} 
""" # Truncate to avoid exceeding token limits
    
    try:
        from google.genai import types
        
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=prompt),
                ],
            ),
        ]
        
        generate_content_config = types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(
                thinking_budget=0,
            ),
            safety_settings=[
                types.SafetySetting(
                    category="HARM_CATEGORY_HARASSMENT",
                    threshold="BLOCK_NONE",
                ),
                types.SafetySetting(
                    category="HARM_CATEGORY_HATE_SPEECH",
                    threshold="BLOCK_NONE",
                ),
                types.SafetySetting(
                    category="HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    threshold="BLOCK_NONE",
                ),
                types.SafetySetting(
                    category="HARM_CATEGORY_DANGEROUS_CONTENT",
                    threshold="BLOCK_NONE",
                ),
            ],
            response_mime_type="application/json",
        )
        
        response_text = ""
        for chunk in client.models.generate_content_stream(
            model=settings.gemini_model_name,
            contents=contents,
            config=generate_content_config,
        ):
            if chunk.text:
                response_text += chunk.text
                
        return json.loads(response_text)
    except (json.JSONDecodeError, AttributeError) as e:
        return {"error": "Could not parse spending analysis from AI.", "raw_response": response_text}
    except Exception as e:
        return {"error": f"Error calling AI for spending analysis: {str(e)}"}

get_payment_forecast_declaration = genai_types.FunctionDeclaration(name="get_payment_forecast", description="Forecasts cash outflow by showing payments due in upcoming periods.", parameters=genai_types.Schema(type=genai_types.Type.OBJECT, properties={}))
def get_payment_forecast(db: Session) -> Dict[str, Any]:
    print("Executing tool: get_payment_forecast")
    today = datetime.now().date()
    q = db.query(
        case(
            (models.Invoice.due_date.between(today, today + timedelta(days=7)), "Next 7 Days"),
            (models.Invoice.due_date.between(today + timedelta(days=8), today + timedelta(days=30)), "Next 8-30 Days"),
            else_="Over 30 Days"
        ).label("period"),
        func.count(models.Invoice.id),
        func.sum(models.Invoice.grand_total)
    ).filter(
        models.Invoice.status == models.DocumentStatus.matched,
        models.Invoice.due_date.isnot(None)
    ).group_by("period").all()
    
    forecast = {row[0]: {"invoice_count": row[1], "total_due": f"${row[2]:,.2f}"} for row in q}
    return forecast

get_learned_heuristics_declaration = genai_types.FunctionDeclaration(
    name="get_learned_heuristics", 
    description="Shows the rules and patterns the system has learned from user behavior, such as consistently approving specific exceptions for a vendor.", 
    parameters=genai_types.Schema(
        type=genai_types.Type.OBJECT,
        properties={
            "vendor_name": genai_types.Schema(type=genai_types.Type.STRING)
        }
    )
)

def get_learned_heuristics(db: Session, vendor_name: Optional[str] = None) -> List[Dict[str, Any]]:
    """Tool implementation to fetch learned heuristics from the database."""
    print(f"Executing tool: get_learned_heuristics for vendor={vendor_name}")
    from app.api.endpoints.learning import get_all_learned_heuristics
    
    # We can reuse the logic from our API endpoint
    results = get_all_learned_heuristics(vendor_name=vendor_name, db=db)
    
    # Format for the LLM
    if not results:
        return [{"message": "No specific heuristics have been learned yet."}]
        
    formatted_results = [schemas.LearnedHeuristic.from_orm(r).model_dump() for r in results]
    return make_json_serializable(formatted_results)

get_notifications_declaration = genai_types.FunctionDeclaration(
    name="get_notifications",
    description="Fetches important, unread notifications, alerts, and suggestions generated by the system's proactive engine. Useful for starting a conversation by checking if there's anything urgent to address."
)

def get_notifications(db: Session) -> List[Dict[str, Any]]:
    """Tool implementation to fetch unread notifications."""
    print("Executing tool: get_notifications")
    from app.api.endpoints.notifications import get_notifications as fetch_notifs
    
    results = fetch_notifs(db=db)
    if not results:
        return [{"message": "There are no new notifications."}]
        
    return [schemas.Notification.from_orm(r).model_dump() for r in results]

# --- Action & Workflow Tools ---
def _update_invoice_status(db: Session, invoice_id: str, new_status: models.DocumentStatus, reason: str) -> Dict[str, Any]:
    invoice = db.query(models.Invoice).filter(models.Invoice.invoice_id == invoice_id).first()
    if not invoice: return {"error": f"Invoice '{invoice_id}' not found."}
    old_status = invoice.status.value
    invoice.status = new_status
    if new_status == models.DocumentStatus.paid:
        invoice.paid_date = datetime.utcnow().date()
    audit_log = models.AuditLog(entity_type='Invoice', entity_id=invoice.invoice_id, user='Copilot', action='Status Changed', details={'from': old_status, 'to': new_status.value, 'reason': reason})
    db.add(audit_log)
    db.commit()
    return {"success": True, "invoice_id": invoice_id, "new_status": new_status.value}

approve_invoice_declaration = genai_types.FunctionDeclaration(name="approve_invoice", description="Approves an invoice for payment.", parameters=genai_types.Schema(type=genai_types.Type.OBJECT, properties={"invoice_id": genai_types.Schema(type=genai_types.Type.STRING), "reason": genai_types.Schema(type=genai_types.Type.STRING)}))
def approve_invoice(db: Session, invoice_id: str, reason: str = "Approved via Copilot") -> Dict[str, Any]:
    print(f"Executing tool: approve_invoice for {invoice_id}")
    return _update_invoice_status(db, invoice_id, models.DocumentStatus.matched, reason)

reject_invoice_declaration = genai_types.FunctionDeclaration(name="reject_invoice", description="Rejects an invoice.", parameters=genai_types.Schema(type=genai_types.Type.OBJECT, properties={"invoice_id": genai_types.Schema(type=genai_types.Type.STRING), "reason": genai_types.Schema(type=genai_types.Type.STRING)}))
def reject_invoice(db: Session, invoice_id: str, reason: str = "Rejected via Copilot") -> Dict[str, Any]:
    print(f"Executing tool: reject_invoice for {invoice_id}")
    return _update_invoice_status(db, invoice_id, models.DocumentStatus.rejected, reason)

update_vendor_tolerance_declaration = genai_types.FunctionDeclaration(name="update_vendor_tolerance", description="Sets a specific price tolerance percentage for a given vendor.", parameters=genai_types.Schema(type=genai_types.Type.OBJECT, properties={"vendor_name": genai_types.Schema(type=genai_types.Type.STRING), "new_tolerance_percent": genai_types.Schema(type=genai_types.Type.NUMBER)}))
def update_vendor_tolerance(db: Session, vendor_name: str, new_tolerance_percent: float) -> Dict[str, Any]:
    print(f"Executing tool: update_vendor_tolerance for {vendor_name}")
    setting = db.query(models.VendorSetting).filter_by(vendor_name=vendor_name).first()
    if not setting:
        setting = models.VendorSetting(vendor_name=vendor_name)
        db.add(setting)
    setting.price_tolerance_percent = new_tolerance_percent
    db.commit()
    return {"success": True, "vendor_name": vendor_name, "new_tolerance_percent": new_tolerance_percent}

edit_purchase_order_declaration = genai_types.FunctionDeclaration(name="edit_purchase_order", description="Edits fields of an existing Purchase Order. Use a JSON object for changes.", parameters=genai_types.Schema(type=genai_types.Type.OBJECT, properties={"po_number": genai_types.Schema(type=genai_types.Type.STRING), "changes": genai_types.Schema(type=genai_types.Type.OBJECT, description="A JSON object of fields to update, e.g., {'line_items': [...]} or {'vendor_name': 'New Name'}")}))
def edit_purchase_order(db: Session, po_number: str, changes: Dict[str, Any]) -> Dict[str, Any]:
    print(f"Executing tool: edit_purchase_order for {po_number} with changes: {changes}")
    po = db.query(models.PurchaseOrder).filter_by(po_number=po_number).first()
    if not po: return {"error": f"PO '{po_number}' not found."}
    for key, value in changes.items():
        if hasattr(po, key):
            setattr(po, key, value)
    db.commit()
    return {"success": True, "po_number": po_number, "updated_fields": list(changes.keys())}

regenerate_po_pdf_declaration = genai_types.FunctionDeclaration(name="regenerate_po_pdf", description="Generates a new PDF file for a Purchase Order after it has been edited.", parameters=genai_types.Schema(type=genai_types.Type.OBJECT, properties={"po_number": genai_types.Schema(type=genai_types.Type.STRING)}))
def regenerate_po_pdf(db: Session, po_number: str) -> Dict[str, Any]:
    print(f"Executing tool: regenerate_po_pdf for {po_number}")
    po = db.query(models.PurchaseOrder).filter_by(po_number=po_number).first()
    if not po: return {"error": f"PO '{po_number}' not found."}
    
    # --- FIX START ---
    # Use the stored raw_data_payload which has the complete structure.
    po_data = po.raw_data_payload
    if not po_data:
        return {"error": f"No raw data payload found for PO '{po_number}'. Cannot regenerate PDF."}

    # If the PO was edited, merge the changes into the payload before regenerating
    po_data['line_items'] = po.line_items # Ensure latest line items are used
    po_data['vendor_name'] = po.vendor_name
    po_data['buyer_name'] = po.buyer_name

    # Recalculate totals based on potentially edited line items
    subtotal = sum(item.get('line_total', 0) for item in po_data.get('line_items', []))
    tax = subtotal * 0.08 # Assuming a static tax rate for regeneration
    po_data['po_subtotal'] = subtotal
    po_data['po_tax'] = tax
    po_data['po_grand_total'] = subtotal + tax
    # --- FIX END ---
    
    # Create a unique filename
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"REGEN_{po_number}_{timestamp}.pdf"
    filepath = os.path.join(GENERATED_DOCS_DIR, filename)

    draw_po_pdf(po_data, filepath)
    
    return {"success": True, "po_number": po_number, "generated_file_path": filepath}

create_payment_proposal_declaration = genai_types.FunctionDeclaration(name="create_payment_proposal", description="Creates a batch of invoices ready for payment based on vendor or due date.", parameters=genai_types.Schema(type=genai_types.Type.OBJECT, properties={"vendor_name": genai_types.Schema(type=genai_types.Type.STRING), "due_in_days": genai_types.Schema(type=genai_types.Type.INTEGER)}))
def create_payment_proposal(db: Session, vendor_name: Optional[str] = None, due_in_days: Optional[int] = None) -> Dict[str, Any]:
    print("Executing tool: create_payment_proposal")
    query = db.query(models.Invoice).filter(models.Invoice.status == models.DocumentStatus.matched)
    if vendor_name:
        query = query.filter(models.Invoice.vendor_name.ilike(f"%{vendor_name}%"))
    if due_in_days is not None:
        due_date = datetime.now().date() + timedelta(days=due_in_days)
        query = query.filter(models.Invoice.due_date <= due_date)
    
    invoices_to_pay = query.all()
    if not invoices_to_pay:
        return {"message": "No approved invoices found matching the criteria."}

    batch_id = f"BATCH-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    total_amount = 0
    invoice_ids = []
    for inv in invoices_to_pay:
        inv.status = models.DocumentStatus.pending_payment
        total_amount += inv.grand_total
        invoice_ids.append(inv.invoice_id)
        db.add(models.AuditLog(entity_type="Invoice", entity_id=inv.invoice_id, user="Copilot", action="Added to Payment Batch", details={"batch_id": batch_id}))
    
    db.commit()
    return {
        "batch_id": batch_id,
        "invoice_count": len(invoice_ids),
        "total_amount": f"${total_amount:,.2f}",
        "invoices_in_batch": invoice_ids
    }

draft_vendor_communication_declaration = genai_types.FunctionDeclaration(
    name="draft_vendor_communication", 
    description="Drafts a professional email to a vendor about an invoice issue. The user should provide the core reason for the communication.", 
    parameters=genai_types.Schema(
        type=genai_types.Type.OBJECT, 
        properties={
            "invoice_id": genai_types.Schema(type=genai_types.Type.STRING), 
            "reason": genai_types.Schema(
                type=genai_types.Type.STRING, 
                description="The specific user-provided reason for the email, e.g., 'Please provide a credit note for the quantity difference' or 'Clarify the extra charges.'"
            )
        }
    )
)

def draft_vendor_communication(db: Session, client: Any, invoice_id: str, reason: str) -> Dict[str, Any]:
    print(f"Executing tool: draft_vendor_communication for {invoice_id} with reason: {reason}")
    dossier = get_invoice_details(db, invoice_id)
    if dossier.get("error"):
        return dossier
        
    vendor_name = dossier.get("summary", {}).get("vendor_name")
    vendor_setting = db.query(models.VendorSetting).filter_by(vendor_name=vendor_name).first()
    vendor_email = vendor_setting.contact_email if vendor_setting else "vendor_contact@example.com"
    
    # Provide the match trace as structured context for the AI
    match_trace_context = json.dumps(dossier.get("match_trace", "No trace available."), indent=2)
    
    prompt = f"""You are a professional Accounts Payable specialist.
Your task is to draft a clear and polite email to a vendor regarding an issue with an invoice.

**Recipient Email:** {vendor_email}
**Subject:** Query regarding Invoice {invoice_id}

**User's Goal for this Email:**
"{reason}"

**Evidence (Technical Match Trace - use this to find specific mismatches):**
{match_trace_context}

**Instructions:**
1.  Start with a polite opening.
2.  Clearly state the user's goal based on the reason provided.
3.  Use the evidence from the match trace to find specific discrepancies (e.g., item names, price/quantity differences) and mention them in the email to support the user's request.
4.  If the trace shows a "Price Mismatch," specify the item, the invoice price, and the PO price.
5.  If the trace shows a "Quantity Mismatch," specify the item, the billed quantity, and the received/ordered quantity.
6.  Conclude with a clear call to action (e.g., "Please provide a corrected invoice," "Please issue a credit note for the difference.").
7.  Maintain a professional and collaborative tone.

Draft the email body now.
"""

    try:
        from google.genai import types
        
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=prompt),
                ],
            ),
        ]
        
        generate_content_config = types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(
                thinking_budget=0,
            ),
            safety_settings=[
                types.SafetySetting(
                    category="HARM_CATEGORY_HARASSMENT",
                    threshold="BLOCK_NONE",
                ),
                types.SafetySetting(
                    category="HARM_CATEGORY_HATE_SPEECH",
                    threshold="BLOCK_NONE",
                ),
                types.SafetySetting(
                    category="HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    threshold="BLOCK_NONE",
                ),
                types.SafetySetting(
                    category="HARM_CATEGORY_DANGEROUS_CONTENT",
                    threshold="BLOCK_NONE",
                ),
            ],
            response_mime_type="text/plain",
        )
        
        response_text = ""
        for chunk in client.models.generate_content_stream(
            model=settings.gemini_model_name,
            contents=contents,
            config=generate_content_config,
        ):
            if chunk.text:
                response_text += chunk.text
                
        return {"draft_email": response_text}
    except Exception as e:
        return {"error": f"Error generating email draft: {str(e)}"}

create_automation_rule_declaration = genai_types.FunctionDeclaration(name="create_automation_rule", description="Creates a new automation rule, e.g., 'auto-approve invoices from a vendor under a certain amount'.", parameters=genai_types.Schema(type=genai_types.Type.OBJECT, properties={"rule_name": genai_types.Schema(type=genai_types.Type.STRING), "vendor_name": genai_types.Schema(type=genai_types.Type.STRING), "condition_json": genai_types.Schema(type=genai_types.Type.STRING, description="A JSON string like '{\"field\": \"grand_total\", \"operator\": \"<\", \"value\": 500}'"), "action": genai_types.Schema(type=genai_types.Type.STRING, description="The action to take, e.g., 'approve'")}))
def create_automation_rule(db: Session, rule_name: str, action: str, vendor_name: Optional[str] = None, condition_json: Optional[str] = None) -> Dict[str, Any]:
    print("Executing tool: create_automation_rule")
    try:
        conditions = json.loads(condition_json) if condition_json else {}
        new_rule = models.AutomationRule(
            rule_name=rule_name,
            vendor_name=vendor_name,
            conditions=conditions,
            action=action
        )
        db.add(new_rule)
        db.commit()
        return {"success": True, "message": f"Automation rule '{rule_name}' created. Note: A separate engine is required to execute these rules."}
    except json.JSONDecodeError:
        return {"error": "Invalid JSON format for condition."}
    except Exception as e:
        db.rollback()
        return {"error": str(e)}

# --- Master Tool Dictionary ---
AVAILABLE_TOOLS = {
    # Analysis
    "get_system_kpis": get_system_kpis,
    "search_invoices": search_invoices,
    "get_invoice_details": get_invoice_details,
    "summarize_vendor_issues": summarize_vendor_issues,
    "flag_potential_anomalies": flag_potential_anomalies,
    "analyze_spending_by_category": analyze_spending_by_category,
    "get_payment_forecast": get_payment_forecast,
    "get_learned_heuristics": get_learned_heuristics,
    "get_notifications": get_notifications,
    # Actions
    "approve_invoice": approve_invoice,
    "reject_invoice": reject_invoice,
    "update_vendor_tolerance": update_vendor_tolerance,
    "edit_purchase_order": edit_purchase_order,
    "regenerate_po_pdf": regenerate_po_pdf,
    "create_payment_proposal": create_payment_proposal,
    "draft_vendor_communication": draft_vendor_communication,
    "create_automation_rule": create_automation_rule,
} 