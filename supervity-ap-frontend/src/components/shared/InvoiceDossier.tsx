"use client";
import { useState } from "react";
import { type Dossier, updateInvoiceStatus } from "@/lib/api";
import { Badge } from "../ui/Badge";
import { Button } from "../ui/Button";
import { MatchTrace } from "./MatchTrace";
import { Loader2 } from "lucide-react";
import toast from "react-hot-toast";

interface InvoiceDossierProps {
  dossier: Dossier;
  onActionComplete: () => void; // Callback to refresh the list
}

export const InvoiceDossier = ({ dossier, onActionComplete }: InvoiceDossierProps) => {
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleStatusUpdate = async (newStatus: 'approved_for_payment' | 'rejected') => {
    setIsSubmitting(true);
    const reason = newStatus === 'approved_for_payment' ? 'Approved via Workbench' : 'Rejected via Workbench';
    
    const promise = updateInvoiceStatus(dossier.summary.invoice_id, {
        new_status: newStatus,
        reason: reason,
    });

    toast.promise(promise, {
        loading: 'Submitting...',
        success: () => {
            onActionComplete(); // Refresh the parent component's list
            return `Invoice successfully ${newStatus === 'approved_for_payment' ? 'approved' : 'rejected'}.`;
        },
        error: (err) => `Failed to update: ${err.message}`,
    });

    try {
        await promise;
    } catch {
        // Error is handled by toast.promise
    } finally {
        setIsSubmitting(false);
    }
  };

  return (
    <div className="p-4 flex flex-col h-full overflow-y-auto">
      {/* Header */}
      <div className="border-b pb-4 mb-4">
        <div className="flex justify-between items-start">
          <div>
            <h2 className="text-2xl font-bold text-black">{dossier.summary.invoice_id}</h2>
            {/* --- FIX IS HERE --- */}
            <p className="text-gray-500">{dossier.summary.vendor_name}</p>
          </div>
          <Badge variant={dossier.summary.status === 'needs_review' ? 'warning' : 'success'}>
            {dossier.summary.status.replace(/_/g, ' ')}
          </Badge>
        </div>
        <div className="mt-4 grid grid-cols-3 gap-4 text-sm">
          <div><span className="font-semibold block text-gray-600">Total</span><span className="font-medium text-gray-900"> ${dossier.summary.grand_total?.toFixed(2)}</span></div>
          <div><span className="font-semibold block text-gray-600">Invoice Date</span><span className="font-medium text-gray-900"> {dossier.summary.invoice_date}</span></div>
          <div><span className="font-semibold block text-gray-600">PO Number</span><span className="font-medium text-gray-900"> {(dossier.documents.po?.data as Record<string, unknown>)?.po_number as string || 'N/A'}</span></div>
        </div>
      </div>

      {/* Match Trace */}
      <div className="mb-6">
        <MatchTrace trace={dossier.match_trace || []} />
      </div>
      
      {/* Actions */}
      <div className="mt-auto pt-4 border-t sticky bottom-0 bg-white">
        <div className="flex gap-4">
          <Button 
            variant="success" 
            className="flex-1" 
            onClick={() => handleStatusUpdate('approved_for_payment')}
            disabled={isSubmitting}
          >
            {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            Approve
          </Button>
          <Button 
            variant="destructive" 
            className="flex-1"
            onClick={() => handleStatusUpdate('rejected')}
            disabled={isSubmitting}
          >
            {isSubmitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            Reject
          </Button>
        </div>
      </div>
    </div>
  );
} 