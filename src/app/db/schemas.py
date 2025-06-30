# src/app/db/schemas.py
from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict
from datetime import date, datetime
from app.db.models import DocumentStatus

# --- Base Schemas ---

class LineItem(BaseModel):
    description: Optional[str] = None
    quantity: Optional[float] = None
    unit_price: Optional[float] = None
    line_total: Optional[float] = None

class InvoiceBase(BaseModel):
    invoice_id: str
    vendor_name: Optional[str] = None
    related_po_numbers: Optional[List[str]] = []
    invoice_date: Optional[date] = None
    grand_total: Optional[float] = None
    line_items: Optional[List[Dict[str, Any]]] = []

class PurchaseOrderBase(BaseModel):
    po_number: str
    vendor_name: Optional[str] = None
    order_date: Optional[date] = None
    line_items: Optional[List[Any]] = []

class GoodsReceiptNoteBase(BaseModel):
    grn_number: str
    po_number: Optional[str] = None
    received_date: Optional[date] = None
    line_items: Optional[List[Any]] = []

class JobBase(BaseModel):
    status: Optional[str] = "processing"
    total_files: Optional[int] = 0
    processed_files: Optional[int] = 0
    summary: Optional[List[Dict[str, Any]]] = None

class AuditLogBase(BaseModel):
    user: str
    action: str
    summary: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


# --- Create Schemas (for receiving data) ---

class InvoiceCreate(InvoiceBase):
    pass

class PurchaseOrderCreate(PurchaseOrderBase):
    pass

class GoodsReceiptNoteCreate(GoodsReceiptNoteBase):
    pass

class JobCreate(JobBase):
    pass

class AuditLogCreate(AuditLogBase):
    entity_type: str
    entity_id: str
    invoice_db_id: Optional[int] = None

class LearnedHeuristicBase(BaseModel):
    vendor_name: str
    exception_type: str
    learned_condition: Dict[str, Any]
    resolution_action: str

class LearnedHeuristicCreate(LearnedHeuristicBase):
    pass

class LearnedHeuristic(LearnedHeuristicBase):
    id: int
    trigger_count: int
    confidence_score: float
    last_applied_at: datetime

    class Config:
        from_attributes = True

class NotificationBase(BaseModel):
    type: str
    message: str
    related_entity_id: Optional[str] = None
    related_entity_type: Optional[str] = None
    proposed_action: Optional[Dict[str, Any]] = None

class Notification(NotificationBase):
    id: int
    is_read: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# --- Full Schemas (for sending data) ---

class Invoice(InvoiceBase):
    id: int
    status: DocumentStatus
    class Config: from_attributes = True

# --- ADD NEW LIGHTWEIGHT SCHEMA FOR LIST VIEWS ---
class InvoiceSummary(BaseModel):
    """A lightweight schema for invoice list views."""
    id: int
    invoice_id: str
    vendor_name: Optional[str] = None
    grand_total: Optional[float] = None
    status: DocumentStatus
    invoice_date: Optional[date] = None
    class Config: from_attributes = True
# --- END NEW SCHEMA ---

class PurchaseOrder(PurchaseOrderBase):
    id: int
    class Config: from_attributes = True

class GoodsReceiptNote(GoodsReceiptNoteBase):
    id: int
    class Config: from_attributes = True

class Job(JobBase):
    id: int
    created_at: datetime
    completed_at: Optional[datetime] = None
    class Config: from_attributes = True

class AuditLog(AuditLogBase):
    id: int
    timestamp: datetime
    entity_type: str
    entity_id: str
    summary: Optional[str] = None
    class Config: from_attributes = True


# --- API Request/Response Schemas ---

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    current_invoice_id: Optional[str] = None

class ToolCall(BaseModel):
    name: str
    args: dict

class ChatResponse(BaseModel):
    conversation_id: str
    response_text: str
    tool_calls: Optional[List[ToolCall]] = None

class UpdateInvoiceStatusRequest(BaseModel):
    new_status: DocumentStatus
    reason: Optional[str] = None

# --- Search Schemas ---

class FilterCondition(BaseModel):
    field: str
    operator: str
    value: Any

class SearchRequest(BaseModel):
    filters: List[FilterCondition] = Field(default_factory=list)
    sort_by: str = 'invoice_date'
    sort_order: str = 'desc'

# --- NEW CONFIGURATION SCHEMAS ---

class VendorSettingBase(BaseModel):
    vendor_name: str
    price_tolerance_percent: Optional[float] = None
    contact_email: Optional[str] = None

class VendorSettingCreate(VendorSettingBase):
    pass

class VendorSettingUpdate(VendorSettingBase):
    id: int  # Required to identify which setting to update

class VendorSetting(VendorSettingBase):
    id: int
    
    class Config:
        from_attributes = True

class AutomationRuleBase(BaseModel):
    rule_name: str
    vendor_name: Optional[str] = None
    conditions: Dict[str, Any]
    action: str
    is_active: bool = True
    source: str = "user"

class AutomationRuleCreate(AutomationRuleBase):
    pass

class AutomationRule(AutomationRuleBase):
    id: int
    
    class Config:
        from_attributes = True

# ADD THESE NEW SCHEMAS
class CommentBase(BaseModel):
    user: str = "System"
    text: str
    type: str = "internal"

class CommentCreate(CommentBase):
    pass

class Comment(CommentBase):
    id: int
    created_at: datetime
    class Config: from_attributes = True

class BatchActionRequest(BaseModel):
    invoice_ids: List[int] 