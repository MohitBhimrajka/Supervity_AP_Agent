"use client";
import { type ComparisonData, updateInvoiceNotes } from "@/lib/api";
import { DocumentViewer } from "@/components/shared/DocumentViewer";
import { LineItemComparisonTable } from "./LineItemComparisonTable";
import { PoDetailsTable } from "./PoDetailsTable";
import { NonPoReview } from "./NonPoReview";
import { Textarea } from "../ui/Textarea";
import { Button } from "../ui/Button";
import { useState } from "react";
import toast from "react-hot-toast";
import { Save } from "lucide-react";
import { cn } from "@/lib/utils";

interface ReviewResolveTabProps {
  comparisonData: ComparisonData | null;
  invoiceDbId: number;
  onDataUpdate: () => void;
}

export const ReviewResolveTab = ({ comparisonData, invoiceDbId, onDataUpdate }: ReviewResolveTabProps) => {
  const [notes, setNotes] = useState(comparisonData?.invoice_notes || "");
  const [isSaving, setIsSaving] = useState(false);

  if (!comparisonData) {
    return <div>Loading comparison data...</div>;
  }

  const isNonPoInvoice = !comparisonData.related_pos || comparisonData.related_pos.length === 0;

  const handleSaveNotes = async () => {
    setIsSaving(true);
    try {
      await updateInvoiceNotes(invoiceDbId, notes);
      toast.success("Notes saved successfully!");
    } catch (error) {
      toast.error(`Failed to save notes: ${error instanceof Error ? error.message : "Unknown error"}`);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 h-full overflow-hidden">
      {/* Left side: Document Viewer */}
      <div className="h-full border rounded-lg flex flex-col bg-white">
        <div className="p-3 border-b bg-gray-50">
            <h3 className="font-semibold text-black">Invoice Document</h3>
        </div>
        <DocumentViewer filePath={comparisonData.related_documents.invoice?.file_path || null} />
      </div>

      {/* Right side: Interactive Data - ADD SCROLLING HERE */}
      <div className="h-full overflow-y-auto pr-2 space-y-6">
        {isNonPoInvoice ? (
            <NonPoReview invoiceDbId={invoiceDbId} initialGlCode={comparisonData.gl_code} />
        ) : (
            <>
                <LineItemComparisonTable comparisonData={comparisonData} onUpdate={onDataUpdate} />
                <PoDetailsTable comparisonData={comparisonData} />
            </>
        )}
        <div>
          <h3 className="text-lg font-semibold mb-2 text-black">Reference Notes</h3>
          <Textarea
            placeholder="Add any internal notes for this invoice..."
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            className="min-h-[100px]"
          />
          <Button onClick={handleSaveNotes} disabled={isSaving} size="sm" className="mt-2">
            <Save className="mr-2 h-4 w-4" />
            {isSaving ? "Saving..." : "Save Notes"}
          </Button>
        </div>
      </div>
    </div>
  );
}; 