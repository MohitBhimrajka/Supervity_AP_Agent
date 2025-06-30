import { z } from "zod";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000/api";

// --- NEW DATE RANGE TYPE ---
export type DateRange = {
    from: string | null;
    to: string | null;
}

// Helper to build date query params
const buildDateQueryParams = (dateRange: DateRange) => {
    const params = new URLSearchParams();
    if (dateRange.from) params.append('start_date', dateRange.from);
    if (dateRange.to) params.append('end_date', dateRange.to);
    return params.toString();
}

// --- START NEW JOB SUMMARY SCHEMA ---
const JobResultSchema = z.object({
  filename: z.string(),
  status: z.enum(['success', 'error']),
  message: z.string(),
  extracted_id: z.string().optional().nullable(),
  affected_pos: z.array(z.string()).optional().nullable(),
});
export type JobResult = z.infer<typeof JobResultSchema>;
// --- END NEW JOB SUMMARY SCHEMA ---

// Define schemas for API responses using Zod for type safety
export const JobSchema = z.object({
  id: z.number(),
  status: z.enum(['pending', 'processing', 'completed', 'failed', 'matching']),
  created_at: z.string(),
  completed_at: z.string().nullable(),
  total_files: z.number(),
  processed_files: z.number(),
  // --- UPDATE THIS LINE ---
  summary: z.array(JobResultSchema).nullable(),
});
export type Job = z.infer<typeof JobSchema>;

const AllJobsResponseSchema = z.array(JobSchema);

/**
 * Uploads an array of files to the backend.
 * @param files - The array of File objects to upload.
 * @returns The created job object.
 */
export async function uploadDocuments(files: File[]): Promise<Job> {
  const formData = new FormData();
  files.forEach(file => {
    formData.append("files", file);
  });

  const response = await fetch(`${API_BASE_URL}/documents/upload`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to upload documents");
  }
  
  const data = await response.json();
  return JobSchema.parse(data);
}

/**
 * Triggers a sync of the sample data directory on the backend.
 * @returns The created job object.
 */
export async function syncSampleData(): Promise<Job> {
  const response = await fetch(`${API_BASE_URL}/documents/sync-sample-data`, {
    method: "POST",
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to start sample data sync");
  }
  
  const data = await response.json();
  return JobSchema.parse(data);
}

/**
 * Fetches the status of a specific job.
 * @param jobId - The ID of the job to fetch.
 * @returns The job object with updated status.
 */
export async function getJobStatus(jobId: number): Promise<Job> {
  const response = await fetch(`${API_BASE_URL}/documents/jobs/${jobId}`);
  if (!response.ok) {
    throw new Error("Failed to fetch job status");
  }
  const data = await response.json();
  return JobSchema.parse(data);
}

/**
 * Fetches a list of recent jobs.
 * @returns An array of job objects.
 */
export async function getAllJobs(): Promise<Job[]> {
    const response = await fetch(`${API_BASE_URL}/documents/jobs`);
    if (!response.ok) {
        throw new Error("Failed to fetch jobs");
    }
    const data = await response.json();
    return AllJobsResponseSchema.parse(data);
}

// Define MatchTraceStepSchema first as it's used in multiple schemas
export const MatchTraceStepSchema = z.object({
  step: z.string(),
  status: z.enum(['PASS', 'FAIL', 'INFO']),
  message: z.string(),
  details: z.record(z.unknown()).optional(),
});
export type MatchTraceStep = z.infer<typeof MatchTraceStepSchema>;

// Make the schema more forgiving of nulls from the DB/API
export const InvoiceSummarySchema = z.object({
    id: z.number(),
    invoice_id: z.string(),
    vendor_name: z.string().nullable(), // Already nullable - good
    grand_total: z.number().nullable(), // Already nullable - good  
    status: z.string(),
    invoice_date: z.string().nullable(), // Already nullable - good
    review_category: z.string().optional().nullable(),
    payment_batch_id: z.string().optional().nullable(),
});
export type InvoiceSummary = z.infer<typeof InvoiceSummarySchema>;
const AllInvoicesSummarySchema = z.array(InvoiceSummarySchema);

// This is the schema we will use for Payment Center and Invoice Explorer
export type Invoice = InvoiceSummary;

// ADD NEW SUGGESTION SCHEMA
export const SuggestionSchema = z.object({
  message: z.string(),
  action: z.string(),
  confidence: z.number(),
});
export type Suggestion = z.infer<typeof SuggestionSchema>;

// --- MAKE SCHEMAS MORE RESILIENT TO NULL/UNDEFINED VALUES ---
export const PoLineItemSchema = z.object({
  description: z.string().optional().nullable(),
  ordered_qty: z.number().optional().nullable(),
  unit_price: z.number().optional().nullable(),
  unit: z.string().optional().nullable(),
  normalized_qty: z.number().optional().nullable(),
  normalized_unit: z.string().optional().nullable(),
  normalized_unit_price: z.number().optional().nullable(),
  po_number: z.string().optional().nullable(),
  po_db_id: z.number().optional().nullable(),
}).passthrough();
export type PoLineItem = z.infer<typeof PoLineItemSchema>;

export const InvoiceLineItemSchema = z.object({
  description: z.string().optional().nullable(),
  quantity: z.number().optional().nullable(),
  unit_price: z.number().optional().nullable(),
  line_total: z.number().optional().nullable(),
  unit: z.string().optional().nullable(),
  normalized_qty: z.number().optional().nullable(),
  normalized_unit: z.string().optional().nullable(),
}).passthrough();
export type InvoiceLineItem = z.infer<typeof InvoiceLineItemSchema>;

const GrnLineItemSchema = z.object({
  description: z.string().optional().nullable(),
  received_qty: z.number().optional().nullable(),
  unit: z.string().optional().nullable(),
  normalized_qty: z.number().optional().nullable(),
  normalized_unit: z.string().optional().nullable(),
  grn_number: z.string().optional().nullable(),
}).passthrough();

export const DocumentPathSchema = z.object({
  file_path: z.string().nullable(),
});
export type DocumentPath = z.infer<typeof DocumentPathSchema>;

export const PoHeaderSchema = z.object({
    id: z.number(),
    po_number: z.string(),
    order_date: z.string().nullable(),
    po_grand_total: z.number().nullable(),
    line_items: z.array(PoLineItemSchema).optional().nullable(),
});
export type PoHeader = z.infer<typeof PoHeaderSchema>;

// This is the new schema for the main workbench data endpoint
export const ComparisonDataSchema = z.object({
  line_item_comparisons: z.array(z.object({
    invoice_line: InvoiceLineItemSchema.nullable(),
    po_line: PoLineItemSchema.nullable(),
    grn_line: GrnLineItemSchema.nullable(),
    po_number: z.string().nullable(),
    grn_number: z.string().nullable(),
  })),
  related_pos: z.array(PoHeaderSchema),
  related_grns: z.array(z.record(z.unknown())),
  related_documents: z.object({
      invoice: DocumentPathSchema.nullable(),
      po: DocumentPathSchema.nullable(),
      grn: DocumentPathSchema.nullable(),
  }),
  // This new field provides all documents for the switcher
  all_related_documents: z.object({
    pos: z.array(z.object({ file_path: z.string().nullable(), po_number: z.string() })),
    grns: z.array(z.object({ file_path: z.string().nullable(), grn_number: z.string() })),
  }),
  match_trace: z.array(MatchTraceStepSchema),
  invoice_notes: z.string().nullable(),
  invoice_status: z.string(),
  gl_code: z.string().nullable().optional(),
  suggestion: SuggestionSchema.nullable(),
});
export type ComparisonData = z.infer<typeof ComparisonDataSchema>;

// More specific schemas for document data
export const InvoiceDataSchema = z.object({
  invoice_number: z.string().optional(),
  po_number: z.string().optional(),
  vendor_name: z.string().optional(),
  grand_total: z.number().optional(),
  invoice_date: z.string().optional(),
}).passthrough(); // Allow additional fields

export const ExceptionSchema = z.object({
  type: z.string(),
  message: z.string(),
  severity: z.enum(['LOW', 'MEDIUM', 'HIGH']).optional(),
  field: z.string().optional(),
}).passthrough();

// --- NEW COLLABORATION SCHEMAS ---
export const CommentSchema = z.object({
    id: z.number(),
    text: z.string(),
    user: z.string(),
    created_at: z.string(),
});
export type Comment = z.infer<typeof CommentSchema>;
const AllCommentsSchema = z.array(CommentSchema);

export const AuditLogSchema = z.object({
  id: z.number(),
  timestamp: z.string(),
  user: z.string(),
  action: z.string(),
  details: z.record(z.unknown()).nullable(),
});
export type AuditLog = z.infer<typeof AuditLogSchema>;
const AllAuditLogsSchema = z.array(AuditLogSchema);

// --- NEW INVOICE FUNCTIONS ---

/**
 * Gets a list of invoices, filterable by status.
 * @param status - The status to filter by (e.g., "needs_review").
 * @returns An array of invoice objects.
 */
// The getInvoices function is now correctly typed
export async function getInvoices(status: string): Promise<Invoice[]> {
    const response = await fetch(`${API_BASE_URL}/invoices/?status=${status}`);
    if (!response.ok) {
        throw new Error("Failed to fetch invoices");
    }
    const data = await response.json();
    return AllInvoicesSummarySchema.parse(data);
}

/**
 * Fetches the invoices processed in a specific job.
 * @param jobId The ID of the job.
 * @returns An array of invoice objects.
 */
export async function getInvoicesForJob(jobId: number): Promise<Invoice[]> {
  const response = await fetch(`${API_BASE_URL}/documents/jobs/${jobId}/invoices`);
  if (!response.ok) {
    throw new Error("Failed to fetch invoices for job");
  }
  const data = await response.json();
  // We can parse it as summary, since that's all the UI component needs
  return AllInvoicesSummarySchema.parse(data);
}



/**
 * Updates the status of an invoice.
 * @param invoiceId - The string-based invoice ID (e.g., INV-AM-98008).
 * @param payload - The payload containing new_status and reason.
 * @returns Success confirmation.
 */
interface UpdateStatusPayload {
    new_status: 'approved_for_payment' | 'rejected';
    reason: string;
}

export async function updateInvoiceStatus(invoiceId: string, payload: UpdateStatusPayload): Promise<{ success: boolean }> {
    // The endpoint in invoices.py is /invoices/{invoice_id}/update-status, where invoice_id is a string
    const response = await fetch(`${API_BASE_URL}/invoices/${invoiceId}/update-status`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
    });

    if (!response.ok) {
        const error = await response.json();
        const errorMessage = error.detail || "Failed to update status";
        // Let's also check for the specific ID mismatch error
        if (typeof errorMessage === 'string' && errorMessage.includes("not found")) {
             throw new Error(`Invoice '${invoiceId}' not found. There might be an ID mismatch.`);
        }
        throw new Error(errorMessage);
    }
    
    return await response.json();
}


// --- NEW WORKBENCH & COLLABORATION FUNCTIONS ---

/**
 * Fetches the detailed line-item comparison data for the workbench.
 * @param invoiceDbId The DATABASE ID (number) of the invoice.
 * @returns The prepared comparison data.
 */
export async function getComparisonData(invoiceDbId: number): Promise<ComparisonData> {
  const response = await fetch(`${API_BASE_URL}/invoices/${invoiceDbId}/comparison-data`);
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to fetch comparison data");
  }
  const data = await response.json();
  return ComparisonDataSchema.parse(data);
}

/**
 * Updates a Purchase Order.
 * @param poDbId The DATABASE ID of the PO to update.
 * @param changes A dictionary of fields to change.
 */
export async function updatePurchaseOrder(poDbId: number, changes: Record<string, unknown>): Promise<unknown> {
  const response = await fetch(`${API_BASE_URL}/documents/purchase-orders/${poDbId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(changes),
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to update Purchase Order");
  }
  return await response.json();
}

/**
 * Updates the notes for an invoice.
 * @param invoiceDbId The DATABASE ID of the invoice.
 * @param notes The new notes text.
 */
export async function updateInvoiceNotes(invoiceDbId: number, notes: string): Promise<unknown> {
  const response = await fetch(`${API_BASE_URL}/invoices/${invoiceDbId}/notes`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ notes }),
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to update notes");
  }
  return await response.json();
}

/**
 * Updates the GL code for a non-PO invoice.
 * @param invoiceDbId The DATABASE ID of the invoice.
 * @param glCode The GL code to assign.
 */
export async function updateGLCode(invoiceDbId: number, glCode: string): Promise<unknown> {
  const response = await fetch(`${API_BASE_URL}/invoices/${invoiceDbId}/gl-code`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ gl_code: glCode }),
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to update GL Code");
  }
  return await response.json();
}

/**
 * Fetches all comments for an invoice.
 * @param invoiceDbId The DATABASE ID of the invoice.
 */
export async function getInvoiceComments(invoiceDbId: number): Promise<Comment[]> {
  const response = await fetch(`${API_BASE_URL}/invoices/${invoiceDbId}/comments`);
  if (!response.ok) throw new Error("Failed to fetch comments");
  return AllCommentsSchema.parse(await response.json());
}

/**
 * Adds a new comment to an invoice.
 * @param invoiceDbId The DATABASE ID of the invoice.
 * @param text The content of the comment.
 */
export async function addInvoiceComment(invoiceDbId: number, text: string): Promise<Comment> {
  const response = await fetch(`${API_BASE_URL}/invoices/${invoiceDbId}/comments`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  });
  if (!response.ok) throw new Error("Failed to add comment");
  return CommentSchema.parse(await response.json());
}

/**
 * Fetches the audit log for an invoice.
 * @param invoiceDbId The DATABASE ID of the invoice.
 */
export async function getInvoiceAuditLog(invoiceDbId: number): Promise<AuditLog[]> {
  const response = await fetch(`${API_BASE_URL}/invoices/${invoiceDbId}/audit-log`);
  if (!response.ok) throw new Error("Failed to fetch audit log");
  return AllAuditLogsSchema.parse(await response.json());
}

/**
 * Fetches a PDF document file from the backend.
 * @param filename - The name of the file to fetch.
 * @returns The URL of the blob for the PDF viewer.
 */
export async function getDocumentFile(filename: string): Promise<string> {
  const response = await fetch(`${API_BASE_URL}/documents/file/${filename}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch file: ${filename}`);
  }
  const blob = await response.blob();
  return URL.createObjectURL(blob);
}

// --- NEW COPILOT SCHEMAS & FUNCTIONS ---
export const CopilotResponseSchema = z.object({
  responseText: z.string(),
  uiAction: z.string(),
  data: z.unknown().nullable(),
});
export type CopilotResponse = z.infer<typeof CopilotResponseSchema>;

interface ChatPayload {
    message: string;
    current_invoice_id?: string | null;
}

/**
 * Sends a message to the Super Agent Copilot.
 * @param payload - The message and optional context.
 * @returns A structured response for the UI to act upon.
 */
export async function postToCopilot(payload: ChatPayload): Promise<CopilotResponse> {
    const response = await fetch(`${API_BASE_URL}/copilot/chat`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to get response from Copilot.");
    }

    const data = await response.json();
    return CopilotResponseSchema.parse(data);
}

// --- MODIFIED DASHBOARD SCHEMAS ---
export const KpiSchema = z.object({
  financial_optimization: z.object({
    discounts_captured: z.string(),
  }),
  operational_efficiency: z.object({
    touchless_invoice_rate_percent: z.number(),
    touchless_rate_change: z.number(), // ADD THIS
    avg_exception_handling_time_hours: z.number(),
    total_processed_invoices: z.number(),
    invoices_in_review_queue: z.number(),
  }),
  vendor_performance: z.object({
    top_vendors_by_exception_rate: z.record(z.string()),
  }),
});
export type Kpis = z.infer<typeof KpiSchema>;

export const SummarySchema = z.object({
    total_invoices: z.number(),
    requires_review: z.number(),
    auto_approved: z.number(),
    pending_match: z.number(),
    total_pos: z.number(),
    total_grns: z.number(),
    total_value_exceptions: z.number(),
});
export type Summary = z.infer<typeof SummarySchema>;

// --- MODIFIED FETCH FUNCTIONS ---
export async function getDashboardKpis(dateRange: DateRange): Promise<Kpis> {
    const query = buildDateQueryParams(dateRange);
    const response = await fetch(`${API_BASE_URL}/dashboard/kpis?${query}`);
    if (!response.ok) throw new Error("Failed to fetch KPIs");
    return KpiSchema.parse(await response.json());
}

export async function getDashboardSummary(dateRange: DateRange): Promise<Summary> {
    const query = buildDateQueryParams(dateRange);
    const response = await fetch(`${API_BASE_URL}/dashboard/summary?${query}`);
    if (!response.ok) throw new Error("Failed to fetch summary");
    return SummarySchema.parse(await response.json());
}

// Exception Summary Schema and Functions
export const ExceptionSummaryItemSchema = z.object({
    name: z.string(),
    count: z.number(),
});
export type ExceptionSummaryItem = z.infer<typeof ExceptionSummaryItemSchema>;
const ExceptionSummaryResponseSchema = z.array(ExceptionSummaryItemSchema);

export async function getExceptionSummary(dateRange: DateRange): Promise<ExceptionSummaryItem[]> {
    const query = buildDateQueryParams(dateRange);
    const response = await fetch(`${API_BASE_URL}/dashboard/exceptions?${query}`);
    if (!response.ok) {
        throw new Error("Failed to fetch exception summary");
    }
    const data = await response.json();
    return ExceptionSummaryResponseSchema.parse(data);
}

export const CostRoiMetricsSchema = z.object({
    total_return_for_period: z.number(),
    total_cost_for_period: z.number(),
});
export type CostRoiMetrics = z.infer<typeof CostRoiMetricsSchema>;

export async function getCostRoiMetrics(dateRange: DateRange): Promise<CostRoiMetrics> {
    const query = buildDateQueryParams(dateRange);
    const response = await fetch(`${API_BASE_URL}/dashboard/cost-roi?${query}`);
    if (!response.ok) {
        throw new Error("Failed to fetch cost ROI metrics");
    }
    const data = await response.json();
    return CostRoiMetricsSchema.parse(data);
}

// --- UPDATED SEARCH FUNCTION ---
interface FilterCondition {
    field: string;
    operator: string;
    value: unknown;
}

interface SearchPayload {
    filters: FilterCondition[];
    sort_by?: string;
    sort_order?: 'asc' | 'desc';
}

export async function searchInvoices(payload: SearchPayload): Promise<Invoice[]> {
    const response = await fetch(`${API_BASE_URL}/documents/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
    });
    if (!response.ok) throw new Error("Failed to search invoices");
    // Use the same summary schema for search results
    return AllInvoicesSummarySchema.parse(await response.json());
}

// --- ADD NEW FUNCTIONS ---

export async function exportToCsv(payload: SearchPayload): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/documents/export-csv`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
    });

    if (!response.ok) {
        throw new Error('Failed to export CSV');
    }

    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'invoice_export.csv';
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
}

interface BatchUpdatePayload {
    invoice_ids: number[];
    new_status: 'approved_for_payment' | 'rejected';
}

export async function batchUpdateInvoiceStatus(payload: BatchUpdatePayload): Promise<{ message: string }> {
    const response = await fetch(`${API_BASE_URL}/invoices/batch-update-status`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to perform bulk update");
    }
    return await response.json();
}

// --- NEW CONFIG & LEARNINGS SCHEMAS AND FUNCTIONS ---

export const VendorSettingSchema = z.object({
    id: z.number(),
    vendor_name: z.string(),
    price_tolerance_percent: z.number().nullable(),
    contact_email: z.string().nullable(),
});
export type VendorSetting = z.infer<typeof VendorSettingSchema>;
const AllVendorSettingsSchema = z.array(VendorSettingSchema);
// ADD CREATE SCHEMA
export const VendorSettingCreateSchema = VendorSettingSchema.omit({ id: true });
export type VendorSettingCreate = z.infer<typeof VendorSettingCreateSchema>;

// --- NEW SCHEMA FOR VENDOR PERFORMANCE ---
export const VendorPerformanceSummarySchema = VendorSettingSchema.extend({
    total_invoices: z.number(),
    exception_rate: z.number(),
    avg_payment_time_days: z.number().nullable(),
});
export type VendorPerformanceSummary = z.infer<typeof VendorPerformanceSummarySchema>;
const AllVendorPerformanceSchema = z.array(VendorPerformanceSummarySchema);

export const AutomationRuleSchema = z.object({
    id: z.number(),
    rule_name: z.string(),
    vendor_name: z.string().nullable(),
    conditions: z.record(z.unknown()),
    action: z.string(),
    is_active: z.boolean().or(z.number()), // Backend uses 1/0, so we accept both
    source: z.string(),
});
export type AutomationRule = z.infer<typeof AutomationRuleSchema>;
const AllAutomationRulesSchema = z.array(AutomationRuleSchema);
// ADD CREATE SCHEMA
export const AutomationRuleCreateSchema = AutomationRuleSchema.omit({ id: true });
export type AutomationRuleCreate = z.infer<typeof AutomationRuleCreateSchema>;

export const LearnedHeuristicSchema = z.object({
    id: z.number(),
    vendor_name: z.string(),
    exception_type: z.string(),
    learned_condition: z.record(z.unknown()),
    resolution_action: z.string(),
    trigger_count: z.number(),
    confidence_score: z.number(),
});
export type LearnedHeuristic = z.infer<typeof LearnedHeuristicSchema>;

// --- NEW SCHEMA FOR AGGREGATED HEURISTICS ---
export const AggregatedHeuristicSchema = LearnedHeuristicSchema.extend({
    id: z.string(), // ID is now a composite string key
    potential_impact: z.number(),
});
export type AggregatedHeuristic = z.infer<typeof AggregatedHeuristicSchema>;
const AllAggregatedHeuristicsSchema = z.array(AggregatedHeuristicSchema);

// --- VENDOR SETTINGS ---
export async function getVendorSettings(): Promise<VendorSetting[]> {
    const response = await fetch(`${API_BASE_URL}/config/vendor-settings`);
    if (!response.ok) throw new Error("Failed to fetch vendor settings");
    return AllVendorSettingsSchema.parse(await response.json());
}

export async function updateVendorSettings(settings: VendorSetting[]): Promise<VendorSetting[]> {
    const response = await fetch(`${API_BASE_URL}/config/vendor-settings`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings),
    });
    if (!response.ok) throw new Error("Failed to update vendor settings");
    return AllVendorSettingsSchema.parse(await response.json());
}

// --- NEW VENDOR SETTING CRUD FUNCTIONS ---

export async function createVendorSetting(settingData: VendorSettingCreate): Promise<VendorSetting> {
    const response = await fetch(`${API_BASE_URL}/config/vendor-settings`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settingData),
    });
    if (!response.ok) throw new Error("Failed to create vendor setting");
    return VendorSettingSchema.parse(await response.json());
}

export async function updateSingleVendorSetting(id: number, settingData: VendorSettingCreate): Promise<VendorSetting> {
    const response = await fetch(`${API_BASE_URL}/config/vendor-settings/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settingData),
    });
    if (!response.ok) throw new Error("Failed to update vendor setting");
    return VendorSettingSchema.parse(await response.json());
}

export async function deleteVendorSetting(id: number): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/config/vendor-settings/${id}`, {
        method: 'DELETE',
    });
    if (!response.ok) throw new Error("Failed to delete vendor setting");
}

// --- NEW VENDOR PERFORMANCE FUNCTION ---
export async function getVendorPerformanceSummary(): Promise<VendorPerformanceSummary[]> {
    const response = await fetch(`${API_BASE_URL}/config/vendor-performance-summary`);
    if (!response.ok) throw new Error("Failed to fetch vendor performance");
    return AllVendorPerformanceSchema.parse(await response.json());
}

// --- AUTOMATION RULES ---
export async function getAutomationRules(): Promise<AutomationRule[]> {
    const response = await fetch(`${API_BASE_URL}/config/automation-rules`);
    if (!response.ok) throw new Error("Failed to fetch automation rules");
    return AllAutomationRulesSchema.parse(await response.json());
}

// --- NEW AUTOMATION RULE CRUD FUNCTIONS ---

export async function createAutomationRule(ruleData: AutomationRuleCreate): Promise<AutomationRule> {
    const response = await fetch(`${API_BASE_URL}/config/automation-rules`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(ruleData),
    });
    if (!response.ok) throw new Error("Failed to create automation rule");
    return AutomationRuleSchema.parse(await response.json());
}

export async function updateAutomationRule(id: number, ruleData: AutomationRuleCreate): Promise<AutomationRule> {
    const response = await fetch(`${API_BASE_URL}/config/automation-rules/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(ruleData),
    });
    if (!response.ok) throw new Error("Failed to update automation rule");
    return AutomationRuleSchema.parse(await response.json());
}

export async function deleteAutomationRule(id: number): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/config/automation-rules/${id}`, {
        method: 'DELETE',
    });
    if (!response.ok) throw new Error("Failed to delete automation rule");
}

// --- LEARNED HEURISTICS ---
export async function getLearnedHeuristics(): Promise<AggregatedHeuristic[]> {
    const response = await fetch(`${API_BASE_URL}/learning/heuristics`);
    if (!response.ok) throw new Error("Failed to fetch learned heuristics");
    return AllAggregatedHeuristicsSchema.parse(await response.json());
}

// --- FIX PAYMENT CENTER FETCH ---
// The /payments/payable endpoint returns a full Invoice object, not a summary.
// Let's create a schema for it.
const PayableInvoiceSchema = z.object({
  id: z.number(),
  invoice_id: z.string(),
  vendor_name: z.string().nullable(),
  due_date: z.string().nullable(),
  grand_total: z.number().nullable(),
}).passthrough(); // Use passthrough() to ignore extra fields
const AllPayableInvoicesSchema = z.array(PayableInvoiceSchema);
export type PayableInvoice = z.infer<typeof PayableInvoiceSchema>;

export async function getPayableInvoices(): Promise<PayableInvoice[]> {
  const response = await fetch(`${API_BASE_URL}/payments/payable`);
  if (!response.ok) throw new Error("Failed to fetch payable invoices");
  const data = await response.json();
  return AllPayableInvoicesSchema.parse(data);
}

export async function createPaymentBatch(invoiceIds: number[]): Promise<{ batch_id: string; processed_invoice_count: number }> {
  const response = await fetch(`${API_BASE_URL}/payments/batches`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ invoice_ids: invoiceIds }),
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to create payment batch");
  }
  return await response.json();
}

export async function getInvoicesByCategory(category: string): Promise<Invoice[]> {
  const formattedCategory = category.toLowerCase().replace(/ /g, '_');
  const response = await fetch(`${API_BASE_URL}/invoices/by-category?category=${formattedCategory}`);
  if (!response.ok) throw new Error("Failed to fetch invoices by category");
  return z.array(InvoiceSummarySchema).parse(await response.json());
}

// Add this new function at the end of the file
export async function batchMarkAsPaid(invoice_ids: number[]): Promise<{ message: string }> {
    const response = await fetch(`${API_BASE_URL}/invoices/batch-mark-as-paid`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ invoice_ids }),
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to mark invoices as paid");
    }
    return await response.json();
}