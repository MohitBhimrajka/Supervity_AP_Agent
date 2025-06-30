"use client";
import { useState, useEffect, useMemo, useCallback } from 'react';
import Link from 'next/link';
import { type InvoiceSummary, searchInvoices, createPaymentBatch, batchMarkAsPaid, batchRematchInvoices, type FilterCondition } from '@/lib/api';
import { useAppContext } from '@/lib/AppContext';
import { QuickLookPanel } from '@/components/explorer/QuickLookPanel';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/Table';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Checkbox } from '@/components/ui/Checkbox';
import { Eye, CheckCircle, Loader2, IndianRupee, RefreshCw, Search, X } from 'lucide-react';
import { format, parseISO } from 'date-fns';
import toast from 'react-hot-toast';
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/Tabs";

type Invoice = InvoiceSummary;

const TABS_CONFIG = [
    { value: 'needs_review', label: 'Needs Review', statusFilter: { field: 'status', operator: 'equals', value: 'needs_review' }},
    { value: 'pending_response', label: 'Pending Response', statusFilter: { field: 'status', operator: 'in', value: ['pending_vendor_response', 'pending_internal_response'] }},
    { value: 'matched', label: 'Matched', statusFilter: { field: 'status', operator: 'equals', value: 'matched' }},
    { value: 'payments', label: 'Payments', statusFilter: { field: 'status', operator: 'in', value: ['pending_payment', 'paid'] }}
];

const getStatusVariant = (status: string) => {
    if (status === 'needs_review') return 'warning';
    if (status === 'matched') return 'success';
    if (status === 'paid') return 'default';
    if (status === 'pending_payment') return 'default';
    if (status.includes('pending')) return 'info';
    if (status === 'rejected') return 'destructive';
    return 'default';
};

export default function InvoiceExplorerPage() {
    const { openCanvas } = useAppContext();
    const [activeTab, setActiveTab] = useState('needs_review');
    const [results, setResults] = useState<Invoice[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [isActing, setIsActing] = useState(false);
    const [selectedRows, setSelectedRows] = useState<Record<number, boolean>>({});
    
    // --- NEW STATE FOR FILTERS ---
    const [searchTerm, setSearchTerm] = useState('');
    const [exceptionFilter, setExceptionFilter] = useState('');
    
    const selectedIds = useMemo(() => Object.keys(selectedRows).filter(id => selectedRows[Number(id)]).map(Number), [selectedRows]);
    
    const handleRowClick = (invoiceId: number) => {
        openCanvas({
            title: "Invoice Quick Look",
            type: 'component',
            content: <QuickLookPanel invoiceDbId={invoiceId} />
        });
    };

    // --- UPDATED FETCH LOGIC ---
    const fetchInvoices = useCallback(async () => {
        setIsLoading(true);
        setSelectedRows({}); // Clear selection on re-fetch
        try {
            const tabConfig = TABS_CONFIG.find(t => t.value === activeTab);
            if (!tabConfig) return;

            const filters: FilterCondition[] = [tabConfig.statusFilter];
            
            if (searchTerm) {
                // This assumes the backend can handle OR logic or a generic search term
                // For this implementation, we'll search the invoice_id field
                filters.push({ field: 'invoice_id', operator: 'contains', value: searchTerm });
            }
            if (exceptionFilter && activeTab === 'needs_review') {
                filters.push({ field: 'review_category', operator: 'equals', value: exceptionFilter });
            }

            const data = await searchInvoices({ filters, sort_by: 'invoice_date', sort_order: 'desc' });
            setResults(data);
        } catch (error) {
            toast.error(`Failed to fetch invoices: ${error instanceof Error ? error.message : "Check console"}`);
        } finally {
            setIsLoading(false);
        }
    }, [activeTab, searchTerm, exceptionFilter]);

    useEffect(() => {
        const timer = setTimeout(() => {
            fetchInvoices();
        }, 300); // Debounce search
        return () => clearTimeout(timer);
    }, [fetchInvoices]);

    const handleTabChange = (newTab: string) => {
        setActiveTab(newTab);
        setSearchTerm(''); // Reset filters when changing tabs
        setExceptionFilter('');
    };

    const handleBulkAction = async () => {
        if (selectedIds.length === 0) return;
        setIsActing(true);
        
        try {
            let res;
            switch (activeTab) {
                case 'needs_review':
                case 'pending_response':
                    res = await batchRematchInvoices(selectedIds);
                    toast.success(res.message);
                    break;
                case 'matched':
                    res = await createPaymentBatch(selectedIds);
                    toast.success(`Payment batch ${res.batch_id} created!`);
                    break;
                case 'payments':
                    res = await batchMarkAsPaid(selectedIds);
                    toast.success(res.message);
                    break;
                default:
                    toast.error("No bulk action available for this tab.");
            }
            fetchInvoices();
        } catch(error) {
            toast.error(`Action failed: ${error instanceof Error ? error.message : "Unknown error"}`);
        } finally {
            setIsActing(false);
        }
    };

    const renderBulkActionButton = () => {
        const buttonClass = "flex items-center gap-2";
        switch (activeTab) {
            case 'needs_review':
            case 'pending_response':
                return <Button onClick={handleBulkAction} disabled={isActing || selectedIds.length === 0} className={buttonClass}><RefreshCw className="h-4 w-4" />Rematch Selected</Button>;
            case 'matched':
                return <Button onClick={handleBulkAction} disabled={isActing || selectedIds.length === 0} className={buttonClass}><IndianRupee className="h-4 w-4" />Create Payment Batch</Button>;
            case 'payments':
                return <Button onClick={handleBulkAction} disabled={isActing || selectedIds.length === 0} className={buttonClass}><CheckCircle className="h-4 w-4" />Mark as Paid</Button>;
            default:
                return null;
        }
    };
    
    const renderFilterBar = () => (
        <div className="flex flex-wrap gap-4 items-center mb-4 p-4 bg-gray-50 rounded-lg border">
            <div className="relative flex-grow min-w-[250px]">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-500" />
                <Input 
                    placeholder="Search by Invoice ID or Vendor..."
                    value={searchTerm}
                    onChange={e => setSearchTerm(e.target.value)}
                    className="pl-10"
                />
            </div>
            {activeTab === 'needs_review' && (
                <div className="flex-grow min-w-[200px]">
                    <select
                        value={exceptionFilter}
                        onChange={e => setExceptionFilter(e.target.value)}
                        className="flex h-10 w-full items-center justify-between rounded-md border border-gray-light bg-white px-3 py-2 text-sm"
                    >
                        <option value="">All Exception Types</option>
                        <option value="data_mismatch">Data Mismatch</option>
                        <option value="missing_document">Missing Document</option>
                        <option value="policy_violation">Policy Violation</option>
                    </select>
                </div>
            )}
             <div className="text-sm font-medium text-gray-600">
                {isLoading ? 'Searching...' : `${results.length} results found`}
            </div>
            {(searchTerm || exceptionFilter) && (
                 <Button variant="ghost" size="sm" onClick={() => { setSearchTerm(''); setExceptionFilter(''); }}>
                    <X className="mr-2 h-4 w-4" /> Clear Filters
                </Button>
            )}
        </div>
    );

    return (
        <div className="space-y-6">
            <Tabs value={activeTab} onValueChange={handleTabChange} className="w-full">
                <TabsList className="grid w-full grid-cols-4">
                    {TABS_CONFIG.map(tab => <TabsTrigger key={tab.value} value={tab.value}>{tab.label}</TabsTrigger>)}
                </TabsList>
                
                <Card className="mt-4">
                    <CardHeader>
                        <CardTitle>{TABS_CONFIG.find(t => t.value === activeTab)?.label} Invoices</CardTitle>
                        <CardDescription>
                            { activeTab === 'needs_review' && 'Invoices that failed automated checks and require manual intervention.' }
                            { activeTab === 'pending_response' && 'Invoices awaiting feedback from vendors or internal teams.' }
                            { activeTab === 'matched' && 'Invoices that passed all checks and are ready for payment.' }
                            { activeTab === 'payments' && 'Invoices that are batched for payment or have been paid.' }
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="pt-0">
                        {renderFilterBar()}
                        <div className="flex justify-between items-center mb-4">
                            <div>
                                {renderBulkActionButton()}
                                {selectedIds.length > 0 && <span className="ml-4 font-medium text-sm text-gray-600">{selectedIds.length} selected</span>}
                            </div>
                        </div>
                        <div className="border rounded-lg overflow-hidden">
                            <Table>
                                <TableHeader>
                                    <TableRow>
                                        <TableHead className="w-12"><Checkbox checked={selectedIds.length === results.length && results.length > 0} onCheckedChange={(c) => setSelectedRows(c ? Object.fromEntries(results.map(r => [r.id, true])) : {})} /></TableHead>
                                        <TableHead>Invoice ID</TableHead>
                                        <TableHead>Vendor</TableHead>
                                        <TableHead>Date</TableHead>
                                        <TableHead>Status</TableHead>
                                        <TableHead className="text-right">Total</TableHead>
                                        <TableHead className="text-center">Action</TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {isLoading ? (
                                        <TableRow><TableCell colSpan={7} className="text-center h-24"><Loader2 className="mx-auto h-6 w-6 animate-spin"/></TableCell></TableRow>
                                    ) : results.length > 0 ? (
                                        results.map(inv => (
                                            <TableRow 
                                                key={inv.id} 
                                                data-state={selectedRows[inv.id] ? 'selected' : ''}
                                                onClick={() => handleRowClick(inv.id)}
                                                className="cursor-pointer"
                                            >
                                                <TableCell onClick={e => e.stopPropagation()}><Checkbox checked={selectedRows[inv.id] || false} onCheckedChange={(c) => setSelectedRows(prev => ({ ...prev, [inv.id]: !!c }))} /></TableCell>
                                                <TableCell className="font-medium">{inv.invoice_id}</TableCell>
                                                <TableCell>{inv.vendor_name}</TableCell>
                                                <TableCell>{inv.invoice_date ? format(parseISO(String(inv.invoice_date)), 'MMM d, yyyy') : 'N/A'}</TableCell>
                                                <TableCell><Badge variant={getStatusVariant(inv.status)}>{inv.status.replace(/_/g, ' ')}</Badge></TableCell>
                                                <TableCell className="text-right font-medium">${inv.grand_total?.toFixed(2)}</TableCell>
                                                <TableCell className="text-center" onClick={e => e.stopPropagation()}>
                                                    <Link href={`/resolution-workbench?invoiceId=${inv.invoice_id}`}><Button variant="ghost" size="sm"><Eye className="h-4 w-4" /></Button></Link>
                                                </TableCell>
                                            </TableRow>
                                        ))
                                    ) : (
                                        <TableRow><TableCell colSpan={7} className="text-center h-24 text-gray-500 font-medium">No invoices found for this queue.</TableCell></TableRow>
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