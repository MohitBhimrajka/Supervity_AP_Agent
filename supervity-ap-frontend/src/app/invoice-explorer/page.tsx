"use client";
import { useState, useEffect, useMemo, useCallback } from 'react';
import Link from 'next/link';
import { type Invoice, searchInvoices, createPaymentBatch, batchMarkAsPaid } from '@/lib/api';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/Table';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Checkbox } from '@/components/ui/Checkbox';
import { Eye, Search, Download, CheckCircle, Loader2, IndianRupee } from 'lucide-react';
import { format, parseISO } from 'date-fns';
import toast from 'react-hot-toast';
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/Tabs";

type SortConfig = {
    key: keyof Invoice;
    direction: 'asc' | 'desc';
};

const TABS = [
    { value: 'all', label: 'Explorer', statusFilter: null },
    { value: 'approved_for_payment', label: 'Ready for Payment', statusFilter: 'approved_for_payment' },
    { value: 'pending_payment', label: 'Pending Payment', statusFilter: 'pending_payment' },
    { value: 'paid', label: 'Paid', statusFilter: 'paid' }
];

const STATUS_OPTIONS = ["needs_review", "approved_for_payment", "pending_payment", "paid", "rejected"];

export default function InvoiceManagerPage() {
    const [activeTab, setActiveTab] = useState('all');
    const [results, setResults] = useState<Invoice[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [isActing, setIsActing] = useState(false);

    const [vendor, setVendor] = useState('');
    const [status, setStatus] = useState('');
    const [totalMin, setTotalMin] = useState('');
    const [totalMax, setTotalMax] = useState('');

    const [sortConfig] = useState<SortConfig>({ key: 'invoice_date', direction: 'desc' });
    const [selectedRows, setSelectedRows] = useState<Record<number, boolean>>({});
    const selectedIds = useMemo(() => Object.keys(selectedRows).filter(id => selectedRows[Number(id)]).map(Number), [selectedRows]);

    const buildFilters = useCallback(() => {
        const filters = [];
        const tabFilter = TABS.find(t => t.value === activeTab)?.statusFilter;
        if (tabFilter) filters.push({ field: 'status', operator: 'equals', value: tabFilter });
        
        if (vendor) filters.push({ field: 'vendor_name', operator: 'contains', value: vendor });
        // Status filter only applies in the 'all' tab
        if (activeTab === 'all' && status) filters.push({ field: 'status', operator: 'equals', value: status });
        if (totalMin) filters.push({ field: 'grand_total', operator: 'gte', value: Number(totalMin) });
        if (totalMax) filters.push({ field: 'grand_total', operator: 'lte', value: Number(totalMax) });
        return filters;
    }, [activeTab, vendor, status, totalMin, totalMax]);

    const fetchInvoices = useCallback(async () => {
        setIsLoading(true);
        setSelectedRows({}); // Clear selection on re-fetch
        try {
            const filters = buildFilters();
            const data = await searchInvoices({ filters, sort_by: String(sortConfig.key), sort_order: sortConfig.direction });
            setResults(data);
        } catch (error) {
            toast.error(`Failed to fetch invoices: ${error instanceof Error ? error.message : "Check console"}`);
        } finally {
            setIsLoading(false);
        }
    }, [buildFilters, sortConfig.key, sortConfig.direction]);

    useEffect(() => {
        fetchInvoices();
    }, [fetchInvoices]);

    const handleBulkAction = async () => {
        if (selectedIds.length === 0) return;
        setIsActing(true);
        
        try {
            if (activeTab === 'approved_for_payment') {
                const res = await createPaymentBatch(selectedIds);
                toast.success(`Payment batch ${res.batch_id} created with ${res.processed_invoice_count} invoices!`);
            } else if (activeTab === 'pending_payment') {
                const res = await batchMarkAsPaid(selectedIds);
                toast.success(res.message);
            }
            fetchInvoices();
        } catch(error) {
            toast.error(`Action failed: ${error instanceof Error ? error.message : "Unknown error"}`);
        } finally {
            setIsActing(false);
        }
    };
    
    const getStatusVariant = (status: string) => {
        if (status === 'needs_review') return 'warning';
        if (status.includes('approved')) return 'success';
        if (status === 'paid') return 'default';
        if (status === 'pending_payment') return 'default';
        if (status === 'rejected') return 'destructive';
        return 'default';
    };

    const renderBulkActionButton = () => {
        if (activeTab === 'approved_for_payment') {
            return <Button onClick={handleBulkAction} disabled={isActing || selectedIds.length === 0}><IndianRupee className="mr-2 h-4 w-4" />Create Payment Batch</Button>;
        }
        if (activeTab === 'pending_payment') {
            return <Button onClick={handleBulkAction} disabled={isActing || selectedIds.length === 0}><CheckCircle className="mr-2 h-4 w-4" />Mark as Paid</Button>;
        }
        return null;
    };

    return (
        <div className="space-y-6">
            <h1 className="text-2xl font-bold text-gray-800">Invoice Manager</h1>
            <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
                <TabsList className="grid w-full grid-cols-4">
                    {TABS.map(tab => <TabsTrigger key={tab.value} value={tab.value}>{tab.label}</TabsTrigger>)}
                </TabsList>
                
                <Card className="mt-4">
                    {activeTab === 'all' && (
                        <CardHeader>
                            <CardTitle>Advanced Search & Filtering</CardTitle>
                             <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4 pt-4">
                                <Input placeholder="Vendor Name..." value={vendor} onChange={e => setVendor(e.target.value)} />
                                <select value={status} onChange={e => setStatus(e.target.value)} className="flex h-10 w-full items-center justify-between rounded-md border border-gray-light bg-transparent px-3 py-2 text-sm">
                                    <option value="">All Statuses</option>
                                    {STATUS_OPTIONS.map(opt => <option key={opt} value={opt}>{opt.replace(/_/g, ' ')}</option>)}
                                </select>
                                <Input type="number" placeholder="Min Total" value={totalMin} onChange={e => setTotalMin(e.target.value)} />
                                <Input type="number" placeholder="Max Total" value={totalMax} onChange={e => setTotalMax(e.target.value)} />
                                <Button onClick={fetchInvoices} disabled={isLoading} className="w-full"><Search className="mr-2 h-4 w-4" />Search</Button>
                            </div>
                        </CardHeader>
                    )}
                    <CardContent className="pt-6">
                        <div className="flex justify-between items-center mb-4">
                            <div>
                                {renderBulkActionButton()}
                                {selectedIds.length > 0 && <span className="ml-4 font-medium text-sm text-gray-600">{selectedIds.length} selected</span>}
                            </div>
                            <Button variant="secondary" onClick={() => {}}><Download className="mr-2 h-4 w-4" />Export CSV</Button>
                        </div>
                        <div className="border rounded-lg overflow-hidden">
                            <Table>
                                <TableHeader>
                                    <TableRow>
                                        <TableHead className="w-12"><Checkbox onCheckedChange={(c) => setSelectedRows(c ? Object.fromEntries(results.map(r => [r.id, true])) : {})} /></TableHead>
                                        <TableHead>Invoice ID</TableHead>
                                        <TableHead>Vendor</TableHead>
                                        <TableHead>Date</TableHead>
                                        <TableHead>Status</TableHead>
                                        <TableHead>Batch ID</TableHead>
                                        <TableHead className="text-right">Total</TableHead>
                                        <TableHead className="text-center">Action</TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {isLoading ? (
                                        <TableRow><TableCell colSpan={8} className="text-center h-24"><Loader2 className="mx-auto h-6 w-6 animate-spin"/></TableCell></TableRow>
                                    ) : results.length > 0 ? (
                                        results.map(inv => (
                                            <TableRow key={inv.id} data-state={selectedRows[inv.id] ? 'selected' : ''}>
                                                <TableCell><Checkbox checked={selectedRows[inv.id] || false} onCheckedChange={(c) => setSelectedRows(prev => ({ ...prev, [inv.id]: !!c }))} /></TableCell>
                                                <TableCell className="font-medium">{inv.invoice_id}</TableCell>
                                                <TableCell>{inv.vendor_name}</TableCell>
                                                <TableCell>{inv.invoice_date ? format(parseISO(inv.invoice_date), 'MMM d, yyyy') : 'N/A'}</TableCell>
                                                <TableCell><Badge variant={getStatusVariant(inv.status)}>{inv.status.replace(/_/g, ' ')}</Badge></TableCell>
                                                <TableCell className="font-mono text-xs">{inv.payment_batch_id || 'N/A'}</TableCell>
                                                <TableCell className="text-right font-medium">${inv.grand_total?.toFixed(2)}</TableCell>
                                                <TableCell className="text-center">
                                                    <Link href={`/resolution-workbench?invoiceId=${inv.invoice_id}`}><Button variant="ghost" size="sm"><Eye className="h-4 w-4" /></Button></Link>
                                                </TableCell>
                                            </TableRow>
                                        ))
                                    ) : (
                                        <TableRow><TableCell colSpan={8} className="text-center h-24 text-gray-500 font-medium">No invoices found for this view.</TableCell></TableRow>
                                    )}
                                </TableBody>
                            </Table>
                        </div>
                    </CardContent>
                </Card>
            </Tabs>
        </div>
    );
} 