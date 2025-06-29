"use client";
import { useState, useEffect } from 'react';
import { getAutomationRules, type AutomationRule } from '@/lib/api';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/Table';
import { Badge } from '../ui/Badge';

export const AutomationRulesTable = () => {
  const [rules, setRules] = useState<AutomationRule[]>([]);
  useEffect(() => { getAutomationRules().then(setRules); }, []);

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Rule Name</TableHead>
          <TableHead>Vendor</TableHead>
          <TableHead>Action</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {rules.map(rule => (
          <TableRow key={rule.id}>
            <TableCell>{rule.rule_name}</TableCell>
            <TableCell>{rule.vendor_name || 'Any'}</TableCell>
            <TableCell><Badge variant="success">{rule.action}</Badge></TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}; 