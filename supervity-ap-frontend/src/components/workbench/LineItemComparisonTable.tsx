"use client";
import { useState } from "react";
import { type ComparisonData, updatePurchaseOrder } from "@/lib/api";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/Table";
import { Input } from "@/components/ui/Input";
import { Button } from "@/components/ui/Button";
import toast from "react-hot-toast";
import { cn } from "@/lib/utils";

interface LineItemComparisonTableProps {
  comparisonData: ComparisonData;
  onUpdate: () => void; // Callback to refresh data after an update
}

// Key for the editable state will be `po_number-item_description`
type EditableFields = {
  [key: string]: {
    ordered_qty?: number;
    unit_price?: number;
  }
};

// Type for line items in PO changes
type LineItem = {
  description: string;
  ordered_qty?: number;
  unit_price?: number;
  line_total?: number;
  [key: string]: unknown;
};

// Type for PO changes structure
type PoChanges = {
  line_items: LineItem[];
};

export const LineItemComparisonTable = ({ comparisonData, onUpdate }: LineItemComparisonTableProps) => {
  const [editableFields, setEditableFields] = useState<EditableFields>({});
  const [isSaving, setIsSaving] = useState(false);

  const handleFieldChange = (poNumber: string, description: string, field: 'ordered_qty' | 'unit_price', value: string) => {
    const key = `${poNumber}-${description}`;
    const numericValue = parseFloat(value);
    if (isNaN(numericValue)) return;

    setEditableFields(prev => ({
      ...prev,
      [key]: {
        ...prev[key],
        [field]: numericValue
      }
    }));
  };

  const handleSaveChanges = async () => {
    setIsSaving(true);
    
    // We need to group changes by PO
    const changesByPoId: Record<number, PoChanges> = {};
    
    for (const key in editableFields) {
        const [poNumber, description] = key.split('-');
        const poToUpdate = comparisonData.related_pos.find(p => p.po_number === poNumber);
        if (!poToUpdate) continue;

        const poId = poToUpdate.id;
        if (!changesByPoId[poId]) {
            // Find the original line items for this PO
            changesByPoId[poId] = { line_items: [...(poToUpdate.line_items || [])] };
        }

        // Find and update the specific line item
        const lineItemIndex = changesByPoId[poId].line_items.findIndex((item: LineItem) => item.description === description);
        if (lineItemIndex !== -1) {
            const updatedItem = { ...changesByPoId[poId].line_items[lineItemIndex], ...editableFields[key] };
            // Recalculate line total
            updatedItem.line_total = (updatedItem.ordered_qty || 0) * (updatedItem.unit_price || 0);
            changesByPoId[poId].line_items[lineItemIndex] = updatedItem;
        }
    }
    
    const promises = Object.entries(changesByPoId).map(([poId, changes]) => 
        updatePurchaseOrder(Number(poId), changes)
    );

    try {
        await Promise.all(promises);
        toast.success("PO changes saved! Re-matching will run in the background.");
        setEditableFields({});
        // Trigger a refresh of the workbench data
        onUpdate();
    } catch (error) {
        toast.error(`Failed to save changes: ${error instanceof Error ? error.message : "Unknown error"}`);
    } finally {
        setIsSaving(false);
    }
  };

  const hasChanges = Object.keys(editableFields).length > 0;

  return (
    <div>
      <div className="flex justify-between items-center mb-2">
        <h3 className="text-lg font-semibold text-black">Line Item Details</h3>
        {hasChanges && (
            <Button onClick={handleSaveChanges} disabled={isSaving} size="sm">
                {isSaving ? "Saving..." : "Save PO Changes"}
            </Button>
        )}
      </div>
      <div className="border rounded-lg overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Description / PO</TableHead>
              <TableHead className="text-center">Inv Qty</TableHead>
              <TableHead className="text-center">Rcvd Qty</TableHead>
              <TableHead className="text-center w-28">Ord Qty</TableHead>
              <TableHead className="text-right w-32">PO Price</TableHead>
              <TableHead className="text-right">Inv Price</TableHead>
              <TableHead className="text-right">Line Total</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {comparisonData.line_item_comparisons.map((line, index) => {
              const poLine = line.po_line || {};
              const invLine = line.invoice_line || {};
              const grnLine = line.grn_line || {};
              
              const key = `${poLine.po_number}-${poLine.description}`;
              const editedQty = editableFields[key]?.ordered_qty;
              const editedPrice = editableFields[key]?.unit_price;

              const isQtyEdited = editedQty !== undefined && editedQty !== poLine.ordered_qty;
              const isPriceEdited = editedPrice !== undefined && editedPrice !== poLine.unit_price;

              return (
                <TableRow key={index} className={cn((isQtyEdited || isPriceEdited) && "bg-blue-primary/5")}>
                    <TableCell>
                        <p className="font-medium">{invLine.description}</p>
                        <p className="text-xs text-gray-500">PO: {line.po_number || 'N/A'}</p>
                    </TableCell>
                    <TableCell className="text-center">{invLine.quantity ?? 'N/A'}</TableCell>
                    <TableCell className="text-center">{grnLine.received_qty ?? 'N/A'}</TableCell>
                    <TableCell>
                        <Input
                            type="number"
                            value={editedQty !== undefined ? editedQty : poLine.ordered_qty ?? ''}
                            onChange={(e) => handleFieldChange(poLine.po_number, poLine.description, 'ordered_qty', e.target.value)}
                            className={cn("text-center h-8", isQtyEdited && "border-blue-primary ring-1 ring-blue-primary")}
                            disabled={!poLine.po_number}
                        />
                    </TableCell>
                    <TableCell>
                        <Input
                            type="number"
                            step="0.01"
                            value={editedPrice !== undefined ? editedPrice : poLine.unit_price ?? ''}
                            onChange={(e) => handleFieldChange(poLine.po_number, poLine.description, 'unit_price', e.target.value)}
                            className={cn("text-right h-8", isPriceEdited && "border-blue-primary ring-1 ring-blue-primary")}
                            disabled={!poLine.po_number}
                        />
                    </TableCell>
                    <TableCell className="text-right">${invLine.unit_price?.toFixed(2) ?? 'N/A'}</TableCell>
                    <TableCell className="text-right font-medium">${invLine.line_total?.toFixed(2) ?? 'N/A'}</TableCell>
                </TableRow>
              )
            })}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}; 