"use client";
import { useState, useEffect } from 'react';
import { getVendorPerformanceSummary, type VendorPerformanceSummary } from '@/lib/api';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/Table';
import { Button } from '@/components/ui/Button';
import { Pencil, PlusCircle, AlertTriangle } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/Card";
import { cn } from '@/lib/utils';

export const VendorSettingsTable = () => {
    const [summary, setSummary] = useState<VendorPerformanceSummary[]>([]);
    
    // We will build out the modal logic later if needed
    // For now, this focuses on displaying the performance data

    useEffect(() => {
        getVendorPerformanceSummary().then(setSummary);
    }, []);

    return (
        <Card>
            <CardHeader>
                <div className="flex justify-between items-center">
                    <div>
                        <CardTitle>Vendor Configuration & Performance</CardTitle>
                        <CardDescription>Manage vendor-specific settings and monitor their performance.</CardDescription>
                    </div>
                    <Button><PlusCircle className="mr-2 h-4 w-4" /> Add Vendor</Button>
                </div>
            </CardHeader>
            <CardContent>
                <div className="border rounded-lg">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Vendor</TableHead>
                          <TableHead className="text-center">Exception Rate</TableHead>
                          <TableHead className="text-center">Total Invoices</TableHead>
                          <TableHead className="text-center">Avg. Pay Time</TableHead>
                          <TableHead className="text-right">Actions</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {summary.map(s => (
                          <TableRow key={s.id}>
                            <TableCell className="font-medium">{s.vendor_name}</TableCell>
                            <TableCell className={cn("text-center font-semibold", s.exception_rate > 20 && "text-orange-warning")}>
                                {s.exception_rate > 20 && <AlertTriangle className="inline-block h-4 w-4 mr-1" />}
                                {s.exception_rate.toFixed(1)}%
                            </TableCell>
                            <TableCell className="text-center">{s.total_invoices}</TableCell>
                            <TableCell className="text-center">{s.avg_payment_time_days ? `${s.avg_payment_time_days} days` : 'N/A'}</TableCell>
                            <TableCell className="text-right">
                                <Button variant="ghost" size="sm"><Pencil className="h-4 w-4" /></Button>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                </div>
            </CardContent>
        </Card>
    );
}; 