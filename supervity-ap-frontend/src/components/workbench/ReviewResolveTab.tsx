"use client";
import { type ComparisonData, updateInvoiceNotes, type PoHeader } from "@/lib/api";
import { DocumentViewer } from "@/components/shared/DocumentViewer";
import { LineItemComparisonTable } from "./LineItemComparisonTable";
import { PoDetailsTable } from "./PoDetailsTable";
import { NonPoReview } from "./NonPoReview";
import { Textarea } from "../ui/Textarea";
import { Button } from "../ui/Button";
import { useState, useEffect } from "react";
import toast from "react-hot-toast";
import { Save } from "lucide-react";
import { SuggestionCallout } from "./SuggestionCallout";
import { ExceptionSummary } from "./ExceptionSummary";
import { StructuredDataViewer } from "./StructuredDataViewer";

interface ReviewResolveTabProps {
  comparisonData: ComparisonData | null;
  invoiceDbId: number;
  onDataUpdate: () => void;
  onApplySuggestion: (action: string) => void;
}

type ActiveDoc = 
    | { type: 'INVOICE'; path: string | null }
    | { type: 'PO'; data: PoHeader | null }
    | { type: 'GRN'; data: Record<string, unknown> | null };

export const ReviewResolveTab = ({ comparisonData, invoiceDbId, onDataUpdate, onApplySuggestion }: ReviewResolveTabProps) => {
  const [notes, setNotes] = useState("");
  const [isSavingNotes, setIsSavingNotes] = useState(false);
  const [activeDoc, setActiveDoc] = useState<ActiveDoc | null>(null);

  useEffect(() => {
    if (comparisonData) {
        setNotes(comparisonData.invoice_notes || "");
        // Default to showing the invoice PDF when data loads
        setActiveDoc({ type: 'INVOICE', path: comparisonData.related_documents.invoice?.file_path ?? null });
    }
  }, [comparisonData]);

  if (!comparisonData) return <div>Loading comparison data...</div>;

  const handleSaveNotes = async () => {
    setIsSavingNotes(true);
    try {
      await updateInvoiceNotes(invoiceDbId, notes);
      toast.success("Notes saved successfully!");
    } catch (error) {
      toast.error(`Failed to save notes: ${error instanceof Error ? error.message : "Unknown error"}`);
    } finally {
      setIsSavingNotes(false);
    }
  };
  
  const isNonPoInvoice = !comparisonData.related_pos || comparisonData.related_pos.length === 0;

  const renderActiveDocument = () => {
    if (!activeDoc) return null;
    switch (activeDoc.type) {
        case 'INVOICE':
            return <DocumentViewer filePath={activeDoc.path} />;
        case 'PO':
            return <StructuredDataViewer documentType="PO" data={activeDoc.data} />;
        case 'GRN':
            return <StructuredDataViewer documentType="GRN" data={activeDoc.data} />;
        default:
            return <div className="p-4">Select a document to view.</div>;
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 h-full overflow-hidden p-4">
      {/* Left side: Smart Viewer */}
      <div className="h-full border rounded-lg flex flex-col bg-white">
        <div className="p-2 border-b bg-gray-50 flex justify-between items-center">
          <h3 className="font-semibold text-black">
            Document Viewer: <span className="text-purple-accent">{activeDoc?.type}</span>
          </h3>
          <div className="flex gap-1">
            <Button size="sm" variant={activeDoc?.type === 'INVOICE' ? 'primary' : 'secondary'} onClick={() => setActiveDoc({type: 'INVOICE', path: comparisonData.related_documents.invoice?.file_path ?? null})}>Invoice</Button>
            <Button size="sm" variant={activeDoc?.type === 'PO' ? 'primary' : 'secondary'} onClick={() => setActiveDoc({type: 'PO', data: comparisonData.related_pos[0] ?? null})} disabled={isNonPoInvoice}>PO</Button>
            <Button size="sm" variant={activeDoc?.type === 'GRN' ? 'primary' : 'secondary'} onClick={() => setActiveDoc({type: 'GRN', data: comparisonData.related_grns[0] ?? null})} disabled={!comparisonData.related_grns || comparisonData.related_grns.length === 0}>GRN</Button>
          </div>
        </div>
        {renderActiveDocument()}
      </div>

      {/* Right side: Interactive Data */}
      <div className="h-full overflow-y-auto pr-2 space-y-6">
        <ExceptionSummary trace={comparisonData.match_trace} />
        
        {comparisonData.suggestion && (
            <SuggestionCallout 
                suggestion={comparisonData.suggestion} 
                onApply={() => onApplySuggestion('approved_for_payment')}
            />
        )}
        
        {/* Always show line items. Comparison table will handle empty PO/GRN data gracefully. */}
        <LineItemComparisonTable comparisonData={comparisonData} onUpdate={onDataUpdate} />

        {isNonPoInvoice ? (
          // If it's a Non-PO invoice, show the GL Code input field.
          <NonPoReview invoiceDbId={invoiceDbId} initialGlCode={comparisonData.gl_code} />
        ) : (
          // If it is a PO invoice, show the PO details table.
          <PoDetailsTable comparisonData={comparisonData} />
        )}
        <div>
          <h3 className="text-lg font-semibold mb-2 text-black">Reference Notes</h3>
          <Textarea
            placeholder="Add any internal notes for this invoice..."
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            className="min-h-[100px]"
          />
          <Button onClick={handleSaveNotes} disabled={isSavingNotes || notes === comparisonData.invoice_notes} size="sm" className="mt-2">
            <Save className="mr-2 h-4 w-4" />
            {isSavingNotes ? "Saving..." : "Save Notes"}
          </Button>
        </div>
      </div>
    </div>
  );
}; 