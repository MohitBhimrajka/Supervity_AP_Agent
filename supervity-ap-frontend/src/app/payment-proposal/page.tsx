"use client";
import { useState, useEffect, useMemo } from 'react';
import { type Invoice, getPayableInvoices, createPaymentBatch } from '@/lib/api';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/Table';
import { Button } from '@/components/ui/Button';
import { Card, CardContent } from '@/components/ui/Card';
import { Checkbox } from "@/components/ui/Checkbox";
import toast from 'react-hot-toast';
import { format, parseISO } from 'date-fns';

export default function PaymentProposalPage() {
    const [invoices, setInvoices] = useState<Invoice[]>([]);
    const [selectedInvoices, setSelectedInvoices] = useState<Record<number, boolean>>({});
    const [isLoading, setIsLoading] = useState(true);
    const [isSubmitting, setIsSubmitting] = useState(false);

    const fetchInvoices = () => {
        setIsLoading(true);
        getPayableInvoices()
            .then(setInvoices)
            .catch(() => toast.error("Failed to load payable invoices."))
            .finally(() => setIsLoading(false));
    };

    useEffect(fetchInvoices, []);

    const selectedIds = useMemo(() => 
        Object.entries(selectedInvoices).filter(([, isSelected]) => isSelected).map(([id]) => Number(id)),
        [selectedInvoices]
    );

    const totalSelectedAmount = useMemo(() => 
        invoices
            .filter(inv => selectedIds.includes(inv.id))
            .reduce((sum, inv) => sum + (inv.grand_total || 0), 0),
        [invoices, selectedIds]
    );

    const handleSelectInvoice = (id: number, isChecked: boolean) => {
        setSelectedInvoices(prev => ({ ...prev, [id]: isChecked }));
    };
    
    const handleCreateBatch = async () => {
        if (selectedIds.length === 0) {
            toast.error("Please select at least one invoice.");
            return;
        }
        setIsSubmitting(true);
        try {
            const result = await createPaymentBatch(selectedIds);
            toast.success(`Batch ${result.batch_id} created with ${result.processed_invoice_count} invoices.`);
            setSelectedInvoices({});
            fetchInvoices(); // Refresh the list
        } catch (error) {
             toast.error(`Failed to create batch: ${error instanceof Error ? error.message : "Unknown error"}`);
        } finally {
            setIsSubmitting(false);
        }
    }

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-start">
                <div>
                    <h1 className="text-3xl font-bold text-black">Payment Proposal</h1>
                    <p className="text-gray-500">Review and batch approved invoices for payment.</p>
                </div>
                <div className="flex items-center gap-4">
                    <div className="text-right">
                         <p className="text-sm font-medium text-gray-500">Selected for Payment</p>
                         <p className="text-2xl font-bold">${totalSelectedAmount.toFixed(2)}</p>
                    </div>
                    <Button onClick={handleCreateBatch} disabled={isSubmitting || selectedIds.length === 0}>
                        {isSubmitting ? "Creating..." : `Create Batch (${selectedIds.length})`}
                    </Button>
                </div>
            </div>

            <Card>
                <CardContent className="mt-6">
                     <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead className="w-12"></TableHead>
                                <TableHead>Invoice ID</TableHead>
                                <TableHead>Vendor</TableHead>
                                <TableHead>Due Date</TableHead>
                                <TableHead className="text-right">Amount</TableHead>
                            </TableRow>
                        </TableHeader>
                         <TableBody>
                            {isLoading ? (
                                <TableRow><TableCell colSpan={5} className="text-center h-24">Loading payable invoices...</TableCell></TableRow>
                            ) : invoices.length === 0 ? (
                                <TableRow><TableCell colSpan={5} className="text-center h-24">No invoices are currently approved for payment.</TableCell></TableRow>
                            ) : (
                                invoices.map(inv => (
                                    <TableRow key={inv.id}>
                                        <TableCell><Checkbox checked={selectedInvoices[inv.id] || false} onCheckedChange={(checked) => handleSelectInvoice(inv.id, !!checked)} /></TableCell>
                                        <TableCell className="font-medium">{inv.invoice_id}</TableCell>
                                        <TableCell>{inv.vendor_name}</TableCell>
                                        <TableCell>{inv.invoice_date ? format(parseISO(inv.invoice_date), 'MMM d, yyyy') : 'N/A'}</TableCell>
                                        <TableCell className="text-right font-semibold">${inv.grand_total?.toFixed(2)}</TableCell>
                                    </TableRow>
                                ))
                            )}
                         </TableBody>
                     </Table>
                </CardContent>
            </Card>
        </div>
    );
} 