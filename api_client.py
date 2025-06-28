# api_client.py
import requests
import streamlit as st
from typing import List, Dict, Any, Optional

# --- Configuration ---
BASE_URL = "http://127.0.0.1:8000/api"

def handle_response(response):
    """Helper to handle API responses and errors."""
    if response.status_code >= 200 and response.status_code < 300:
        return response.json()
    st.error(f"API Error ({response.status_code}): {response.text}")
    return None

# --- Dashboard Endpoints ---
def get_kpis():
    response = requests.get(f"{BASE_URL}/dashboard/kpis")
    return handle_response(response)

# --- Document & Job Endpoints ---
def upload_documents(files):
    file_list = [("files", (file.name, file.getvalue(), file.type)) for file in files]
    response = requests.post(f"{BASE_URL}/documents/upload", files=file_list)
    return handle_response(response)

def get_jobs():
    response = requests.get(f"{BASE_URL}/documents/jobs")
    return handle_response(response)

def get_job_status(job_id: int):
    response = requests.get(f"{BASE_URL}/documents/jobs/{job_id}")
    return handle_response(response)

# --- Invoice Endpoints ---
def get_invoices(status: Optional[str] = None):
    params = {"status": status} if status else {}
    response = requests.get(f"{BASE_URL}/invoices/", params=params)
    return handle_response(response)

def get_recent_invoices(limit: int = 25):
    """Get recent invoices for the data explorer default view"""
    response = requests.get(f"{BASE_URL}/invoices/")
    result = handle_response(response)
    if result:
        return result[:limit]  # Limit the results on the client side
    return None

def get_invoice_dossier(invoice_id: str):
    response = requests.get(f"{BASE_URL}/invoices/{invoice_id}/dossier")
    return handle_response(response)

def update_invoice_status(invoice_id: str, new_status: str, reason: str):
    payload = {"new_status": new_status, "reason": reason}
    response = requests.post(f"{BASE_URL}/invoices/{invoice_id}/update-status", json=payload)
    return handle_response(response)

def approve_invoice(invoice_id: str, reason: str = "Approved via Workbench"):
    """Approve an invoice for payment"""
    return update_invoice_status(invoice_id, "approved_for_payment", reason)

def reject_invoice(invoice_id: str, reason: str = "Rejected via Workbench"):
    """Reject an invoice"""
    return update_invoice_status(invoice_id, "rejected", reason)

# --- Learning & Notifications ---
def get_heuristics():
    response = requests.get(f"{BASE_URL}/learning/heuristics")
    return handle_response(response)

def get_notifications():
    response = requests.get(f"{BASE_URL}/notifications/")
    return handle_response(response)

def mark_notification_read(notification_id: int):
    response = requests.post(f"{BASE_URL}/notifications/{notification_id}/mark-read")
    return handle_response(response)

# --- Copilot Endpoint ---
def copilot_chat(message: str, current_invoice_id: Optional[str] = None):
    payload = {"message": message, "current_invoice_id": current_invoice_id}
    response = requests.post(f"{BASE_URL}/copilot/chat", json=payload)
    return handle_response(response)

# --- Data Explorer ---
def search_invoices(filters: List[Dict]):
    payload = {"filters": filters}
    response = requests.post(f"{BASE_URL}/documents/search", json=payload)
    return handle_response(response)

# --- Configuration ---
def get_vendor_settings():
    response = requests.get(f"{BASE_URL}/config/vendor-settings")
    return handle_response(response)

def update_vendor_settings(settings_data: List[Dict]):
    response = requests.put(f"{BASE_URL}/config/vendor-settings", json=settings_data)
    return handle_response(response)

def get_automation_rules():
    response = requests.get(f"{BASE_URL}/config/automation-rules")
    return handle_response(response)

def create_automation_rule(rule_data: Dict):
    response = requests.post(f"{BASE_URL}/config/automation-rules", json=rule_data)
    return handle_response(response)

# --- Placeholder functions for advanced features (to prevent errors) ---
def get_insights_stats():
    """Placeholder for future insights statistics endpoint"""
    return None

def dismiss_notification(notification_id: int):
    """Placeholder for dismissing notifications (for now, just mark as read)"""
    return mark_notification_read(notification_id)

def get_vendor_insights():
    """Placeholder for future vendor insights endpoint"""
    return None

def get_queue_stats():
    """Placeholder for queue statistics"""
    return None 