"use client";

import { useState, useEffect } from "react";
import { type Invoice, getInvoices } from "@/lib/api";
import toast from 'react-hot-toast';

import { cn } from "@/lib/utils";
import { Button } from "../ui/Button";

interface InvoiceListProps {
    selectedInvoiceId: string | null;
    onInvoiceSelect: (invoice: Invoice) => void;
    refreshKey?: number;
}

// --- MODIFIED HELPER FUNCTION ---
const getCategoryVariant = (category: string | null | undefined): string => {
    switch (category) {
        case 'missing_document':
        case 'policy_violation':
            return 'border-l-4 border-pink-destructive'; // Use brand color
        case 'data_mismatch':
            return 'border-l-4 border-orange-warning'; // Use brand color
        default:
            return 'border-l-4 border-transparent';
    }
}

export const InvoiceList = ({ selectedInvoiceId, onInvoiceSelect, refreshKey }: InvoiceListProps) => {
    const [invoices, setInvoices] = useState<Invoice[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [statusFilter, setStatusFilter] = useState("needs_review");

    useEffect(() => {
        const fetchInvoices = async () => {
            if (!statusFilter) return; 

            setIsLoading(true);
            try {
                const data = await getInvoices(statusFilter);
                setInvoices(data);
            } catch (error) {
                console.error(error);
                toast.error("Failed to fetch invoices");
            } finally {
                setIsLoading(false);
            }
        };
        fetchInvoices();
    }, [statusFilter, refreshKey]);

    return (
        <div className="flex flex-col h-full">
            <div className="p-4 border-b">
                <h3 className="text-lg font-semibold">Work Queue</h3>
                <div className="flex gap-2 mt-2">
                    <Button size="sm" variant={statusFilter === 'needs_review' ? 'primary' : 'secondary'} onClick={() => setStatusFilter('needs_review')}>Review</Button>
                    <Button size="sm" variant={statusFilter === 'matched' ? 'primary' : 'secondary'} onClick={() => setStatusFilter('matched')}>Approved</Button>
                </div>
            </div>
            <div className="flex-grow overflow-y-auto">
                {isLoading ? (
                    <p className="p-4 text-gray-800 font-medium">Loading invoices...</p>
                ) : invoices.length === 0 ? (
                    <div className="p-4 text-center text-gray-800">
                        <p className="font-medium">No invoices found for status: {statusFilter.replace(/_/g, ' ')}</p>
                        <p className="text-sm mt-1 text-gray-700">Try selecting a different filter or upload documents in the Document Hub.</p>
                    </div>
                ) : (
                    <ul className="p-2 space-y-2">
                        {invoices.map(invoice => (
                            <li key={invoice.invoice_id} onClick={() => onInvoiceSelect(invoice)}
                                className={cn(
                                    "p-3 rounded-lg cursor-pointer transition-colors",
                                    getCategoryVariant(invoice.review_category), // Apply color-coding
                                    selectedInvoiceId === invoice.invoice_id
                                        ? "bg-blue-primary/10"
                                        : "bg-white hover:bg-gray-50"
                                )}>
                                <div className="flex justify-between items-center mb-1">
                                    <p className="font-semibold">{invoice.invoice_id}</p>
                                    <p className="font-bold text-lg">${invoice.grand_total?.toFixed(2)}</p>
                                </div>
                                <div className="flex justify-between items-center text-sm text-gray-800">
                                    <span className="font-medium">{invoice.vendor_name}</span>
                                    <span className="font-medium">{invoice.invoice_date}</span>
                                </div>
                            </li>
                        ))}
                    </ul>
                )}
            </div>
        </div>
    );
}; 