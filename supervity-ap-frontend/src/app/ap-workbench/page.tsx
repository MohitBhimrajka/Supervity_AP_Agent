"use client";
import React, { useState, useEffect, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { InvoiceList } from '@/components/shared/InvoiceList';
import { InvoiceDossier } from '@/components/shared/InvoiceDossier';
import { DocumentViewer } from '@/components/shared/DocumentViewer';
import { type Dossier, getInvoiceDossier } from '@/lib/api';
import { useAppContext } from '@/lib/AppContext';
import { Loader2, FileSearch } from 'lucide-react';

function WorkbenchContent() {
    const { setCurrentInvoiceId } = useAppContext();
    const searchParams = useSearchParams();
    const initialInvoiceId = searchParams.get('invoiceId');

    const [selectedInvoiceId, setSelectedInvoiceId] = useState<string | null>(null);
    const [dossier, setDossier] = useState<Dossier | null>(null);
    const [isLoadingDossier, setIsLoadingDossier] = useState(false);
    const [refreshKey, setRefreshKey] = useState(0);

    const handleActionComplete = () => {
        // Refresh the invoice list and clear the selected invoice
        setRefreshKey(prev => prev + 1);
        setSelectedInvoiceId(null);
        setDossier(null);
    };

    useEffect(() => {
        // Set the initial invoice ID from the URL if it exists
        if (initialInvoiceId && !selectedInvoiceId) {
            setSelectedInvoiceId(initialInvoiceId);
        }
    }, [initialInvoiceId, selectedInvoiceId]);

    useEffect(() => {
        // Update the global context whenever the selected invoice changes
        setCurrentInvoiceId(selectedInvoiceId);

        const fetchDossier = async () => {
            if (!selectedInvoiceId) {
                setDossier(null);
                return;
            }
            setIsLoadingDossier(true);
            try {
                const data = await getInvoiceDossier(selectedInvoiceId);
                setDossier(data);
            } catch (error) {
                console.error("Failed to fetch dossier", error);
                setDossier(null);
            } finally {
                setIsLoadingDossier(false);
            }
        };

        fetchDossier();
    }, [selectedInvoiceId, setCurrentInvoiceId]);

    return (
        // The main container needs to be fixed height
        <div className="h-full max-h-[calc(100vh-8rem)] flex flex-col">
            <div className="flex-shrink-0">
                <h1 className="text-3xl font-bold text-black mb-6">AP Workbench</h1>
            </div>
            {/* This container needs to handle overflow */}
            <div className="flex-grow grid grid-cols-1 lg:grid-cols-10 gap-6 overflow-hidden">
                {/* Panel 1: Work Queue - This already has overflow handled inside InvoiceList */}
                <div className="lg:col-span-3 h-full rounded-lg flex flex-col bg-white border">
                    <InvoiceList 
                        selectedInvoiceId={selectedInvoiceId} 
                        onInvoiceSelect={setSelectedInvoiceId}
                        refreshKey={refreshKey}
                    />
                </div>

                {/* Main content area */}
                <div className="lg:col-span-7 h-full grid grid-cols-1 xl:grid-cols-7 gap-6 overflow-hidden">
                    {/* Panel 2: Dossier View - This is where scrolling is needed */}
                    <div className="xl:col-span-4 h-full border rounded-lg bg-white overflow-y-auto">
                        {isLoadingDossier ? (
                            <div className="h-full flex items-center justify-center text-gray-800"><Loader2 className="w-8 h-8 animate-spin" /></div>
                        ) : dossier ? (
                            <InvoiceDossier 
                                dossier={dossier} 
                                onActionComplete={handleActionComplete}
                            />
                        ) : (
                            <div className="p-4 h-full flex flex-col items-center justify-center text-center text-gray-800">
                                <FileSearch className="w-16 h-16 text-gray-600 mb-4" />
                                <h3 className="text-lg font-semibold text-black">Select an Invoice</h3>
                                <p className="text-gray-800 font-medium">Details and actions will appear here once you select an invoice from the queue.</p>
                            </div>
                        )}
                    </div>
                    {/* Panel 3: Document Viewer */}
                    <div className="xl:col-span-3 h-full border rounded-lg flex flex-col bg-white overflow-hidden">
                        <DocumentViewer dossier={dossier} />
                    </div>
                </div>
            </div>
        </div>
    );
}

export default function ApWorkbenchPage() {
    return (
        <Suspense fallback={<div className="flex h-full w-full items-center justify-center"><Loader2 className="w-10 h-10 animate-spin" /></div>}>
            <WorkbenchContent />
        </Suspense>
    )
} 