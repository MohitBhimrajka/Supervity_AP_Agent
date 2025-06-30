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
  onUpdate: () => void;
}

type EditableFields = {
  [key: string]: {
    ordered_qty?: number;
    unit_price?: number;
  }
};

type PoChanges = {
  line_items: Record<string, unknown>[];
};

const MismatchCell = ({ children, isMismatch }: { children: React.ReactNode, isMismatch: boolean }) => (
    <TableCell className={cn("text-center font-medium", isMismatch && "bg-orange-warning/20 rounded")}>
        {children}
    </TableCell>
);

export const LineItemComparisonTable = ({ comparisonData, onUpdate }: LineItemComparisonTableProps) => {
  const [editableFields, setEditableFields] = useState<EditableFields>({});
  const [isSaving, setIsSaving] = useState(false);

  const handleFieldChange = (poDbId: number, description: string, field: 'ordered_qty' | 'unit_price', value: string) => {
    const key = `${poDbId}-${description}`;
    const numericValue = parseFloat(value);
    if (isNaN(numericValue)) return;

    setEditableFields(prev => ({ ...prev, [key]: { ...prev[key], [field]: numericValue } }));
  };

  const handleSaveChanges = async () => {
    setIsSaving(true);
    const changesByPoId: Record<number, PoChanges> = {};

    for (const key in editableFields) {
        const [poDbIdStr, description] = key.split(/-(.*)/);
        const poDbId = Number(poDbIdStr);
        const poToUpdate = comparisonData.related_pos.find(p => p.id === poDbId);
        if (!poToUpdate) continue;
        if (!changesByPoId[poDbId]) {
            changesByPoId[poDbId] = { line_items: JSON.parse(JSON.stringify(poToUpdate.line_items || [])) };
        }
        const lineItemIndex = changesByPoId[poDbId].line_items.findIndex((item: Record<string, unknown>) => item.description === description);
        if (lineItemIndex !== -1) {
            const updatedItem = { ...changesByPoId[poDbId].line_items[lineItemIndex], ...editableFields[key] } as Record<string, unknown>;
            updatedItem.line_total = ((updatedItem.ordered_qty as number) || 0) * ((updatedItem.unit_price as number) || 0);
            changesByPoId[poDbId].line_items[lineItemIndex] = updatedItem;
        }
    }
    
    const promises = Object.entries(changesByPoId).map(([poId, changes]) => updatePurchaseOrder(Number(poId), changes));

    try {
        await Promise.all(promises);
        toast.success("PO changes saved! Re-matching will run in the background.");
        setEditableFields({});
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
        {hasChanges && <Button onClick={handleSaveChanges} disabled={isSaving} size="sm">{isSaving ? "Saving..." : "Save PO Changes"}</Button>}
      </div>
      <div className="border rounded-lg overflow-x-auto">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Description / PO</TableHead>
              <TableHead className="text-center">Inv Qty</TableHead>
              <TableHead className="text-center">Rcvd Qty</TableHead>
              <TableHead className="text-center" style={{minWidth: '120px'}}>Ord Qty</TableHead>
              <TableHead className="text-right" style={{minWidth: '120px'}}>Inv Price</TableHead>
              <TableHead className="text-right" style={{minWidth: '120px'}}>PO Price</TableHead>
              <TableHead className="text-right">Line Total</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {comparisonData.line_item_comparisons.map((line, index) => {
              const poLine = line.po_line;
              const invLine = line.invoice_line;
              const grnLine = line.grn_line;
              if (!invLine) return null;
              const key = `${poLine?.po_db_id}-${poLine?.description}`;
              const editedQty = editableFields[key]?.ordered_qty;
              const editedPrice = editableFields[key]?.unit_price;
              const isQtyEdited = editedQty !== undefined && poLine && editedQty !== poLine.ordered_qty;
              const isPriceEdited = editedPrice !== undefined && poLine && editedPrice !== poLine.unit_price;
              const qtyMismatch = Math.abs((invLine.normalized_qty ?? 0) - (grnLine?.normalized_qty ?? poLine?.normalized_qty ?? 0)) > 0.01;
              const priceMismatch = Math.abs((invLine.unit_price ?? 0) - (poLine?.unit_price ?? 0)) > 0.01;
              return (
                <TableRow key={index} className="align-top">
                    <TableCell>
                        <p className="font-medium truncate">{invLine.description ?? 'N/A'}</p>
                        <p className="text-xs text-gray-500">PO: {line.po_number || 'N/A'}</p>
                    </TableCell>
                    <MismatchCell isMismatch={qtyMismatch}>
                        <p>{invLine.quantity ?? '–'}</p>
                        <p className="text-xs text-gray-500">{invLine.unit}</p>
                    </MismatchCell>
                    <MismatchCell isMismatch={qtyMismatch}>
                        <p>{grnLine?.received_qty ?? '–'}</p>
                        <p className="text-xs text-gray-500">{grnLine?.unit}</p>
                    </MismatchCell>
                    <TableCell>
                        {poLine ? (
                            <div className="flex flex-col items-center gap-1">
                                <Input type="number" value={editedQty ?? poLine.ordered_qty ?? ''}
                                    onChange={(e) => poLine.po_db_id && poLine.description && handleFieldChange(poLine.po_db_id, poLine.description, 'ordered_qty', e.target.value)}
                                    className={cn("text-center h-8 w-full", isQtyEdited && "border-purple-accent ring-1 ring-purple-accent")} />
                                <span className="text-xs text-gray-500">{poLine.unit}</span>
                            </div>
                        ) : 'N/A'}
                    </TableCell>
                    <MismatchCell isMismatch={priceMismatch}>
                       <p>${(invLine.unit_price ?? 0).toFixed(2)}</p>
                    </MismatchCell>
                    <TableCell>
                        {poLine ? (
                             <div className="flex flex-col items-end gap-1">
                                <Input type="number" step="0.01" value={editedPrice ?? poLine.unit_price ?? ''}
                                    onChange={(e) => poLine.po_db_id && poLine.description && handleFieldChange(poLine.po_db_id, poLine.description, 'unit_price', e.target.value)}
                                    className={cn("text-right h-8 w-full", isPriceEdited && "border-purple-accent ring-1 ring-purple-accent")} />
                             </div>
                        ) : 'N/A'}
                    </TableCell>
                    <TableCell className="text-right font-bold">${(invLine.line_total ?? 0).toFixed(2)}</TableCell>
                </TableRow>
              )
            })}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}; 