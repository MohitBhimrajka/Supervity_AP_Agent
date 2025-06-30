"use client";
import { type AuditLog, type ComparisonData, getInvoiceAuditLog, getInvoiceComments, addInvoiceComment, requestVendorResponse, requestInternalResponse } from "@/lib/api";
import { useEffect, useState } from "react";
import { Button } from "../ui/Button";
import { Textarea } from "../ui/Textarea";
import toast from "react-hot-toast";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../ui/Card";
import { Mail, Loader2, Users, MessageSquare } from 'lucide-react';
import { AuditTrailItem } from './AuditTrailItem';

interface WorkflowAuditTabProps {
  invoiceDbId: number;
  onActionComplete: () => void;
  comparisonData: ComparisonData | null;
}

export const WorkflowAuditTab = ({ invoiceDbId, onActionComplete, comparisonData }: WorkflowAuditTabProps) => {
    const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
    const [isLoading, setIsLoading] = useState(true);

    const [internalComment, setInternalComment] = useState("");
    const [vendorEmail, setVendorEmail] = useState("");
    const [internalReview, setInternalReview] = useState("");

    const [isSubmitting, setIsSubmitting] = useState<string | null>(null);

    const generateSuggestion = (type: 'price' | 'quantity') => {
        if (!comparisonData) return;
        
        const firstFailure = comparisonData.match_trace.find(
            step => step.status === 'FAIL' && step.step.toLowerCase().includes(type)
        );

        if (firstFailure) {
            const details = firstFailure.details || {};
            const itemDesc = (details.item_description as string) || 'the item';
            if (type === 'price') {
                const poPrice = (details.po_price as number)?.toFixed(2);
                setVendorEmail(`Hello,\n\nCould you please clarify the unit price for '${itemDesc}' on this invoice? Our records show a price of $${poPrice} on the PO.\n\nThanks,`);
            } else {
                 const sourceQty = details.grn_qty ?? details.po_qty;
                 const source = details.grn_qty ? 'received' : 'ordered';
                 setVendorEmail(`Hello,\n\nThere appears to be a quantity discrepancy for '${itemDesc}' on this invoice. We billed for ${details.invoice_qty}, but our records show ${sourceQty} were ${source}.\n\nCould you please advise or issue a credit note?\n\nThanks,`);
            }
        }
    };

    useEffect(() => {
        const fetchData = async () => {
            if (!invoiceDbId) return;
            setIsLoading(true);
            try {
                const [, auditLogsData] = await Promise.all([
                    getInvoiceComments(invoiceDbId),
                    getInvoiceAuditLog(invoiceDbId),
                ]);
                // Comments are not displayed in the current UI, so we don't need to store them
                setAuditLogs(auditLogsData);
            } catch {
                toast.error("Failed to load workflow & audit data.");
            } finally {
                setIsLoading(false);
            }
        };
        fetchData();
    }, [invoiceDbId]);

    const handleAction = async (type: 'vendor' | 'internal' | 'comment') => {
        let actionPromise;
        let message;

        setIsSubmitting(type);

        try {
            switch (type) {
                case 'vendor':
                    if (!vendorEmail.trim()) { toast.error("Vendor message cannot be empty."); return; }
                    actionPromise = requestVendorResponse(invoiceDbId, vendorEmail);
                    message = "Message sent to vendor queue.";
                    break;
                case 'internal':
                    if (!internalReview.trim()) { toast.error("Internal review message cannot be empty."); return; }
                    actionPromise = requestInternalResponse(invoiceDbId, internalReview);
                    message = "Sent for internal review.";
                    break;
                case 'comment':
                    if (!internalComment.trim()) { toast.error("Comment cannot be empty."); return; }
                    actionPromise = addInvoiceComment(invoiceDbId, internalComment);
                    message = "Comment added!";
                    break;
                default:
                    return;
            }

            await actionPromise;
            toast.success(message);
            onActionComplete(); // This will close the detail view and refresh the queue list
        } catch (error) {
            toast.error(`Action failed: ${error instanceof Error ? error.message : "Unknown error"}`);
        } finally {
            setIsSubmitting(null);
        }
    };
    
    if (isLoading) return <div className="p-4"><Loader2 className="animate-spin" /> Loading...</div>;

    return (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 p-4">
            <div className="space-y-6">
                {/* Email Communication */}
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2"><Mail className="w-5 h-5 text-purple-accent" /> Email Communication</CardTitle>
                        <CardDescription>Draft a message to the vendor. This will change the invoice status to &apos;Pending Vendor Response&apos;.</CardDescription>
                        <div className="flex gap-2 pt-2">
                            <Button size="sm" variant="secondary" onClick={() => generateSuggestion('price')}>Suggest Price Query</Button>
                            <Button size="sm" variant="secondary" onClick={() => generateSuggestion('quantity')}>Suggest Qty Query</Button>
                        </div>
                    </CardHeader>
                    <CardContent className="space-y-3">
                        <Textarea value={vendorEmail} onChange={e => setVendorEmail(e.target.value)} placeholder="e.g., Please clarify the price for &apos;Cutting Disc&apos;..." />
                        <Button onClick={() => handleAction('vendor')} disabled={!!isSubmitting}>
                            {isSubmitting === 'vendor' ? <Loader2 className="mr-2 h-4 w-4 animate-spin"/> : <Mail className="mr-2 h-4 w-4"/>}
                            Send to Vendor
                        </Button>
                    </CardContent>
                </Card>

                {/* Internal Communication */}
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2"><Users className="w-5 h-5 text-cyan-accent" /> Internal Team Communication</CardTitle>
                        <CardDescription>Route this to another team for approval. This will change the invoice status to &apos;Pending Internal Response&apos;.</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-3">
                        <Textarea value={internalReview} onChange={e => setInternalReview(e.target.value)} placeholder="e.g., @Procurement - can you please confirm receipt of these goods?" />
                        <Button onClick={() => handleAction('internal')} disabled={!!isSubmitting}>
                            {isSubmitting === 'internal' ? <Loader2 className="mr-2 h-4 w-4 animate-spin"/> : <Users className="mr-2 h-4 w-4"/>}
                            Send for Internal Review
                        </Button>
                    </CardContent>
                </Card>
            </div>
            {/* Audit History */}
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2"><MessageSquare className="w-5 h-5" /> Workflow & Audit History</CardTitle>
                    <CardDescription>A complete log of all automated and manual actions taken on this invoice.</CardDescription>
                </CardHeader>
                <CardContent>
                    <div className="max-h-[500px] overflow-y-auto pr-2">
                        {auditLogs.length > 0 ? (
                            auditLogs.map((log, index) => (
                                <AuditTrailItem key={log.id} log={log} isLast={index === auditLogs.length - 1} />
                            ))
                        ) : (
                            <p className="text-sm text-gray-500">No audit history found for this invoice.</p>
                        )}
                    </div>
                    <div className="mt-6 border-t pt-4">
                        <Textarea value={internalComment} onChange={e => setInternalComment(e.target.value)} placeholder="Add an internal note... (this will be logged)" />
                        <Button onClick={() => handleAction('comment')} disabled={!!isSubmitting} size="sm" className="mt-2">
                            {isSubmitting === 'comment' && <Loader2 className="mr-2 h-4 w-4 animate-spin"/>} Add Note
                        </Button>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}; 