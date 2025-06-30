"use client";
import { type MatchTraceStep } from "@/lib/api";
import { AlertCircle, FileWarning, BadgeDollarSign, Scale } from "lucide-react";

const getIconForStep = (step: string) => {
    if (step.toLowerCase().includes("quantity")) return <Scale className="h-5 w-5 text-orange-600" />;
    if (step.toLowerCase().includes("price")) return <BadgeDollarSign className="h-5 w-5 text-orange-600" />;
    if (step.toLowerCase().includes("document") || step.toLowerCase().includes("item match") || step.toLowerCase().includes("timing")) return <FileWarning className="h-5 w-5 text-orange-600" />;
    return <AlertCircle className="h-5 w-5 text-orange-600" />;
}

// Function to generate a more user-friendly message
const generateFriendlyMessage = (failure: MatchTraceStep): string => {
    const details = failure.details || {};
    
    if (failure.step.includes("Price Match")) {
        const invPrice = (details.inv_price as number)?.toFixed(2);
        const poPrice = (details.po_price as number)?.toFixed(2);
        return `The invoice price ($${invPrice}) does not match the PO price ($${poPrice}) for this item.`;
    }

    if (failure.step.includes("Quantity Match")) {
        let invQty, invUnit, compQty, compUnit, source;
        if (details.grn_qty !== undefined) {
            invQty = details.invoice_qty;
            invUnit = details.invoice_unit;
            compQty = details.grn_qty;
            compUnit = details.grn_unit;
            source = "received";
        } else {
            invQty = details.invoice_qty;
            invUnit = details.invoice_unit;
            compQty = details.po_qty;
            compUnit = details.po_unit;
            source = "ordered";
        }
        return `The billed quantity (${invQty} ${invUnit}) does not match the quantity ${source} (${compQty} ${compUnit}).`;
    }
    
    // Fallback to the original message for other errors
    return failure.message;
}

export const ExceptionSummary = ({ trace }: { trace: MatchTraceStep[] }) => {
    const failures = trace.filter(step => step.status === 'FAIL');

    if (failures.length === 0) {
        return null;
    }

    // Filter out the generic "Final Result" failure to avoid redundancy
    const specificFailures = failures.filter(f => f.step !== 'Final Result');
    
    // If only "Final Result" is a failure, it means something passed that shouldn't have. Show it.
    const displayFailures = specificFailures.length > 0 ? specificFailures : failures;

    return (
        <div className="space-y-3">
             <h3 className="text-lg font-semibold text-black">Resolution Required</h3>
            {displayFailures.map((failure, index) => (
                <div key={index} className="p-4 rounded-lg bg-orange-warning/10 border-l-4 border-orange-warning">
                    <div className="flex items-start gap-3">
                        <div className="flex-shrink-0 mt-1">
                            {getIconForStep(failure.step)}
                        </div>
                        <div>
                            <h4 className="font-semibold text-orange-700">{failure.step}</h4>
                            <p className="text-sm text-gray-700 mt-1">{generateFriendlyMessage(failure)}</p>
                        </div>
                    </div>
                </div>
            ))}
        </div>
    );
}; 