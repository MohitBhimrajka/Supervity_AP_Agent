"use client";
import { useState, useEffect } from 'react';
import { getVendorSettings, type VendorSetting } from '@/lib/api';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/Table';

export const VendorSettingsTable = () => {
    const [settings, setSettings] = useState<VendorSetting[]>([]);
    useEffect(() => { getVendorSettings().then(setSettings); }, []);

    return (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Vendor</TableHead>
              <TableHead>Price Tolerance (%)</TableHead>
              <TableHead>Contact Email</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {settings.map(s => (
              <TableRow key={s.id}>
                <TableCell>{s.vendor_name}</TableCell>
                <TableCell>{s.price_tolerance_percent?.toFixed(1) || 'Default'}</TableCell>
                <TableCell>{s.contact_email || 'N/A'}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
    );
} 