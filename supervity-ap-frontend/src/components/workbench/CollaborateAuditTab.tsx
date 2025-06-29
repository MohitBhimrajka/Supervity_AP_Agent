"use client";
import { type AuditLog, type Comment, getInvoiceAuditLog, getInvoiceComments, addInvoiceComment, postToCopilot } from "@/lib/api";
import { useEffect, useState } from "react";
import { Button } from "../ui/Button";
import { Textarea } from "../ui/Textarea";
import { format } from "date-fns";
import toast from "react-hot-toast";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/Card";
import ReactMarkdown from 'react-markdown';
import { Mail, Loader2 } from 'lucide-react';

interface CollaborateAuditTabProps {
  invoiceDbId: number;
  invoiceId: string;
  vendorName: string;
}

export const CollaborateAuditTab = ({ invoiceDbId, invoiceId, vendorName }: CollaborateAuditTabProps) => {
    const [comments, setComments] = useState<Comment[]>([]);
    const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
    const [newComment, setNewComment] = useState("");
    const [isLoading, setIsLoading] = useState(true);
    const [draftEmail, setDraftEmail] = useState<string | null>(null);
    const [isDrafting, setIsDrafting] = useState(false);

    useEffect(() => {
        const fetchData = async () => {
            setIsLoading(true);
            try {
                const [commentsData, auditLogsData] = await Promise.all([
                    getInvoiceComments(invoiceDbId),
                    getInvoiceAuditLog(invoiceDbId),
                ]);
                setComments(commentsData);
                setAuditLogs(auditLogsData);
            } catch {
                toast.error("Failed to load collaboration data.");
            } finally {
                setIsLoading(false);
            }
        };
        fetchData();
    }, [invoiceDbId]);

    const handleAddComment = async () => {
        if (!newComment.trim()) return;
        try {
            const addedComment = await addInvoiceComment(invoiceDbId, newComment);
            setComments(prev => [...prev, addedComment]);
            setNewComment("");
            toast.success("Comment added!");
        } catch {
            toast.error("Failed to add comment.");
        }
    };

    const handleDraftEmail = async () => {
        setIsDrafting(true);
        setDraftEmail(null);
        try {
            const response = await postToCopilot({
                message: `Draft a polite but firm email to the vendor ${vendorName} regarding all discrepancies found in invoice ${invoiceId}. Clearly state the issues and the required actions.`,
                current_invoice_id: invoiceId
            });
            // The tool returns data in a specific shape, let's extract it.
            if (response.uiAction === 'DISPLAY_MARKDOWN' && typeof response.data === 'object' && response.data && 'draft_email' in response.data) {
                setDraftEmail(response.data.draft_email as string);
                toast.success("Email draft generated!");
            } else {
                 setDraftEmail("Sorry, I couldn't generate a draft. The AI returned an unexpected format.");
                 toast.error("Failed to generate draft.");
            }
        } catch (error) {
            const message = error instanceof Error ? error.message : "An unknown error occurred.";
            setDraftEmail(`Error generating email: ${message}`);
            toast.error("Failed to generate draft.");
        } finally {
            setIsDrafting(false);
        }
    };
    
    if (isLoading) return <div>Loading...</div>

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-6">
                <Card>
                    <CardHeader>
                        <CardTitle>Vendor Communication</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <Button onClick={handleDraftEmail} disabled={isDrafting}>
                            {isDrafting ? <Loader2 className="mr-2 h-4 w-4 animate-spin"/> : <Mail className="mr-2 h-4 w-4"/>}
                            {isDrafting ? "Thinking..." : "Draft Email for Discrepancies"}
                        </Button>
                        {draftEmail && (
                            <div className="mt-4 p-4 border rounded-lg bg-gray-50 text-sm prose max-w-none">
                                <ReactMarkdown>{draftEmail}</ReactMarkdown>
                            </div>
                        )}
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader>
                        <CardTitle>Internal Comments</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="space-y-3 max-h-96 overflow-y-auto pr-2">
                            {comments.map(c => (
                                <div key={c.id} className="bg-gray-100 p-3 rounded-lg">
                                    <p className="text-sm">{c.text}</p>
                                    <p className="text-xs text-gray-500 mt-1">
                                        - {c.user} on {format(new Date(c.created_at), 'MMM d, yyyy h:mm a')}
                                    </p>
                                </div>
                            ))}
                        </div>
                        <div className="space-y-2">
                            <Textarea value={newComment} onChange={e => setNewComment(e.target.value)} placeholder="Add a comment..."/>
                            <Button onClick={handleAddComment} size="sm">Add Comment</Button>
                        </div>
                    </CardContent>
                </Card>
            </div>
            <Card>
                <CardHeader>
                    <CardTitle>Audit History</CardTitle>
                </CardHeader>
                <CardContent>
                    <ul className="space-y-3 max-h-[500px] overflow-y-auto pr-2">
                        {auditLogs.map(log => (
                            <li key={log.id} className="text-sm">
                                <span className="font-semibold text-black">{log.action}</span> by <span className="font-medium text-gray-800">{log.user}</span>
                                <span className="block text-xs text-gray-500">{format(new Date(log.timestamp), 'MMM d, yyyy h:mm a')}</span>
                            </li>
                        ))}
                    </ul>
                </CardContent>
            </Card>
        </div>
    );
}; 