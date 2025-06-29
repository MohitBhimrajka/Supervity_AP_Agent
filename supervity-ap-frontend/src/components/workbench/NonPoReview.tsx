"use client";
import { useState } from "react";
import { Input } from "../ui/Input";
import { Button } from "../ui/Button";
import { updateGLCode } from "@/lib/api";
import toast from "react-hot-toast";

interface NonPoReviewProps {
  invoiceDbId: number;
  initialGlCode?: string | null;
}

export const NonPoReview = ({ invoiceDbId, initialGlCode }: NonPoReviewProps) => {
    const [glCode, setGlCode] = useState(initialGlCode || "");
    const [isSaving, setIsSaving] = useState(false);

    const handleSave = async () => {
        if (!glCode.trim()) {
            toast.error("GL Code cannot be empty.");
            return;
        }
        setIsSaving(true);
        try {
            await updateGLCode(invoiceDbId, glCode);
            toast.success("GL Code saved!");
        } catch (error) {
            toast.error(`Failed to save GL Code: ${error instanceof Error ? error.message : "Unknown error"}`);
        } finally {
            setIsSaving(false);
        }
    };

    return (
        <div className="p-6 bg-white border rounded-lg">
            <h3 className="text-lg font-semibold text-black">Non-PO Invoice Review</h3>
            <p className="text-sm text-gray-500 mb-4">This invoice is not linked to a Purchase Order. Please apply a General Ledger (GL) code before approving.</p>
            <div className="flex items-center gap-2">
                <Input 
                    placeholder="Enter GL Code (e.g., 5010-Office-Supplies)"
                    value={glCode}
                    onChange={(e) => setGlCode(e.target.value)}
                />
                <Button onClick={handleSave} disabled={isSaving}>
                    {isSaving ? "Saving..." : "Save GL Code"}
                </Button>
            </div>
        </div>
    );
}; 