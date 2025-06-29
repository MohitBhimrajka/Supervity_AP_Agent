"use client";
import { useState, useEffect } from 'react';
import Link from 'next/link';
import { type Invoice, searchInvoices, getInvoices } from '@/lib/api';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/Table';
import { Card, CardContent, CardDescription, CardHeader } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Eye, Search } from 'lucide-react';
import { format, parseISO } from 'date-fns';

export default function InvoiceExplorerPage() {
    const [results, setResults] = useState<Invoice[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [vendor, setVendor] = useState('');
    const [status, setStatus] = useState('');

    const fetchAndSetInvoices = async (filters: Array<{ field: string; operator: string; value: string }> = []) => {
        setIsLoading(true);
        try {
            const data = filters.length > 0
                ? await searchInvoices(filters)
                : await getInvoices(""); // Fetch all if no filters
            setResults(data);
        } catch (error) {
            console.error(error);
            // In a real app, show a toast notification here
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        fetchAndSetInvoices();
    }, []);

    const handleSearch = () => {
        const filters = [];
        if (vendor) filters.push({ field: 'vendor_name', operator: 'contains', value: vendor });
        if (status) filters.push({ field: 'status', operator: 'equals', value: status });
        fetchAndSetInvoices(filters);
    };

    const getStatusVariant = (status: string) => {
        if (status === 'needs_review') return 'warning';
        if (status === 'approved_for_payment' || status === 'paid') return 'success';
        if (status === 'rejected') return 'destructive';
        return 'default';
    };

    return (
        <div className="space-y-6">
            <h1 className="text-3xl font-bold text-black">Invoice Explorer</h1>
            <Card>
                <CardHeader>
                    <CardDescription>Perform custom queries across all invoice data.</CardDescription>
                </CardHeader>
                <CardContent className="flex flex-col sm:flex-row gap-4">
                    <Input placeholder="Vendor Name..." value={vendor} onChange={e => setVendor(e.target.value)} />
                    <Input placeholder="Status (e.g., needs_review)" value={status} onChange={e => setStatus(e.target.value)} />
                    <Button onClick={handleSearch} disabled={isLoading} className="w-full sm:w-auto">
                        <Search className="mr-2 h-4 w-4" />
                        Search
                    </Button>
                </CardContent>
            </Card>
            <Card>
                <CardContent className="mt-6">
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead>Invoice ID</TableHead>
                                <TableHead>Vendor</TableHead>
                                <TableHead>Date</TableHead>
                                <TableHead>Status</TableHead>
                                <TableHead>PO / GRN</TableHead>
                                <TableHead className="text-right">Total</TableHead>
                                <TableHead className="text-center">Action</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {isLoading ? (
                                <TableRow>
                                    <TableCell colSpan={7} className="text-center h-24">Loading...</TableCell>
                                </TableRow>
                            ) : results.length > 0 ? (
                                results.map(inv => (
                                    <TableRow key={inv.id}>
                                        <TableCell className="font-medium">{inv.invoice_id}</TableCell>
                                        <TableCell>{inv.vendor_name}</TableCell>
                                        <TableCell>
                                            {inv.invoice_date ? format(parseISO(inv.invoice_date), 'MMM d, yyyy') : 'N/A'}
                                        </TableCell>
                                        <TableCell>
                                            <Badge variant={getStatusVariant(inv.status)}>
                                                {inv.status.replace(/_/g, ' ')}
                                            </Badge>
                                        </TableCell>
                                        <TableCell className="text-sm text-gray-800 font-medium">
                                            <div>{inv.po_number || 'N/A'}</div>
                                            <div>{inv.grn_number || 'N/A'}</div>
                                        </TableCell>
                                        <TableCell className="text-right font-medium">${inv.grand_total?.toFixed(2)}</TableCell>
                                        <TableCell className="text-center">
                                            <Link href={`/ap-workbench?invoiceId=${inv.invoice_id}`}>
                                                <Button variant="ghost" size="sm">
                                                    <Eye className="h-4 w-4" />
                                                </Button>
                                            </Link>
                                        </TableCell>
                                    </TableRow>
                                ))
                            ) : (
                                <TableRow>
                                    <TableCell colSpan={7} className="text-center h-24 text-gray-800 font-medium">No invoices found.</TableCell>
                                </TableRow>
                            )}
                        </TableBody>
                    </Table>
                </CardContent>
            </Card>
        </div>
    );
} 