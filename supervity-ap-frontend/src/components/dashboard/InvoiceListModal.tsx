"use client";
import { type Invoice } from "@/lib/api";
import { Modal } from "@/components/ui/Modal";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/Table";
import { Button } from "@/components/ui/Button";
import Link from "next/link";
import { Eye } from "lucide-react";

interface InvoiceListModalProps {
  isOpen: boolean;
  onClose: () => void;
  invoices: Invoice[];
  category: string;
}

export const InvoiceListModal = ({ isOpen, onClose, invoices, category }: InvoiceListModalProps) => {
  return (
    <Modal isOpen={isOpen} onClose={onClose} title={`Invoices with Exception: ${category}`}>
      <div className="max-h-[60vh] overflow-y-auto">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Invoice ID</TableHead>
              <TableHead>Vendor</TableHead>
              <TableHead className="text-right">Total</TableHead>
              <TableHead className="text-center">Action</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {invoices.length > 0 ? invoices.map(inv => (
              <TableRow key={inv.id}>
                <TableCell className="font-medium">{inv.invoice_id}</TableCell>
                <TableCell>{inv.vendor_name}</TableCell>
                <TableCell className="text-right">${inv.grand_total?.toFixed(2)}</TableCell>
                <TableCell className="text-center">
                  <Link href={`/resolution-workbench?invoiceId=${inv.invoice_id}`} passHref>
                    <Button variant="ghost" size="sm"><Eye className="h-4 w-4" /></Button>
                  </Link>
                </TableCell>
              </TableRow>
            )) : <TableRow><TableCell colSpan={4} className="text-center h-24">No invoices found for this category.</TableCell></TableRow>}
          </TableBody>
        </Table>
      </div>
    </Modal>
  );
}; 