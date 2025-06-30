"use client";
import React, { useState, useEffect, Suspense, useCallback } from 'react';
import { useSearchParams, useRouter, usePathname } from 'next/navigation';
import { InvoiceList } from '@/components/shared/InvoiceList';
import { type ComparisonData, getComparisonData, updateInvoiceStatus, type InvoiceSummary, getInvoiceByStringId } from '@/lib/api';
import { useAppContext } from '@/lib/AppContext';
import { Loader2, FileSearch, CheckCircle, XCircle, ArrowLeft, Bot } from 'lucide-react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/Tabs';
import { Button } from '@/components/ui/Button';
import toast from 'react-hot-toast';
import { ReviewResolveTab } from '@/components/workbench/ReviewResolveTab';
import { MatchVisualizerTab } from '@/components/workbench/MatchVisualizerTab';
import { WorkflowAuditTab } from '@/components/workbench/WorkflowAuditTab';
import { cn } from '@/lib/utils';

// Using InvoiceSummary as the type for our selected invoice state
type Invoice = InvoiceSummary;

function WorkbenchContent() {
    const { setCurrentInvoiceId, openCanvas } = useAppContext();
    const searchParams = useSearchParams();
    const router = useRouter();
    const pathname = usePathname();
    
    // State to hold the invoice object, whether from the queue or URL
    const [activeInvoice, setActiveInvoice] = useState<Invoice | null>(null);
    const [comparisonData, setComparisonData] = useState<ComparisonData | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [queueRefreshKey, setQueueRefreshKey] = useState(0); // To refresh the left-side list
    const [dataRefreshTrigger, setDataRefreshTrigger] = useState(0); // To refresh the main content

    // This callback is passed to child components to trigger a full refresh
    const forceDataRefresh = useCallback(() => setDataRefreshTrigger(prev => prev + 1), []);

    const invoiceIdFromUrl = searchParams.get('invoiceId');

    // Effect to handle loading from URL or selection
    useEffect(() => {
        if (invoiceIdFromUrl) {
            setIsLoading(true);
            getInvoiceByStringId(invoiceIdFromUrl)
                .then(invoiceData => {
                    setActiveInvoice(invoiceData);
                    setCurrentInvoiceId(invoiceData.invoice_id);
                })
                .catch(() => {
                    toast.error(`Could not find invoice: ${invoiceIdFromUrl}`);
                    router.push(pathname); // Clear the URL param if not found
                });
        } else {
            // If URL has no ID, clear any active invoice
            setActiveInvoice(null);
            setComparisonData(null);
            setCurrentInvoiceId(null);
            setIsLoading(false);
        }
    }, [invoiceIdFromUrl, setCurrentInvoiceId, router, pathname]);

    // Effect to fetch comparison data whenever the active invoice changes
    useEffect(() => {
        if (activeInvoice) {
            setIsLoading(true);
            setComparisonData(null); // Clear old data
            getComparisonData(activeInvoice.id)
                .then(setComparisonData)
                .catch(err => toast.error(`Error loading details: ${err.message}`))
                .finally(() => setIsLoading(false));
        }
    }, [activeInvoice, dataRefreshTrigger]);

    const handleInvoiceSelect = (invoice: Invoice) => {
        router.push(`${pathname}?invoiceId=${invoice.invoice_id}`);
    };

    const handleCloseDetailView = useCallback(() => {
        router.push(pathname);
    }, [router, pathname]);

    const handleActionComplete = useCallback(() => {
        setQueueRefreshKey(prev => prev + 1); // Refresh the queue on the left
        handleCloseDetailView();
    }, [handleCloseDetailView]);

    const handleStatusUpdate = async (newStatus: 'matched' | 'rejected') => {
        if (!activeInvoice) return;
        setIsSubmitting(true);
        const reason = `Manually ${newStatus === 'matched' ? 'Approved' : 'Rejected'} via Workbench`;
        
        try {
            await updateInvoiceStatus(activeInvoice.invoice_id, { new_status: newStatus, reason });
            toast.success(`Invoice successfully ${newStatus === 'matched' ? 'approved' : 'rejected'}.`);
            handleActionComplete();
        } catch (error) {
             toast.error(`Failed to update: ${error instanceof Error ? error.message : "Unknown error"}`);
        } finally {
            setIsSubmitting(false);
        }
    };

    const renderMainContent = () => {
        if (!invoiceIdFromUrl) {
             return (
                <div className="p-4 h-full flex flex-col items-center justify-center text-center text-gray-800 bg-white border rounded-lg">
                    <FileSearch className="w-16 h-16 text-gray-600 mb-4" />
                    <h3 className="text-lg font-semibold text-black">Select an Invoice</h3>
                    <p className="text-gray-medium font-medium">Select an invoice from the work queue to begin, or link directly to one from another page.</p>
                </div>
            );
        }
        
        if (isLoading || !comparisonData || !activeInvoice) {
            return <div className="h-full flex items-center justify-center text-gray-800"><Loader2 className="w-8 h-8 animate-spin" /> <span className="ml-3">Loading Invoice Data...</span></div>;
        }

        return (
            <>
                <div className="flex-shrink-0 bg-white p-4 rounded-lg border flex justify-between items-center">
                    <div className="flex items-center gap-4">
                        <Button variant="ghost" size="sm" onClick={handleCloseDetailView} className="p-2 h-auto"><ArrowLeft className="w-5 h-5" /></Button>
                        <div>
                            <h2 className="text-2xl font-bold text-black">{activeInvoice.invoice_id}</h2>
                            <p className="text-gray-medium font-medium">{activeInvoice.vendor_name}</p>
                        </div>
                    </div>
                    <div className="flex items-center gap-2">
                        <Button variant="success" onClick={() => handleStatusUpdate('matched')} disabled={isSubmitting}><CheckCircle className="mr-2 h-4 w-4"/> Approve</Button>
                        <Button variant="destructive" onClick={() => handleStatusUpdate('rejected')} disabled={isSubmitting}><XCircle className="mr-2 h-4 w-4"/> Reject</Button>
                        <Button variant="secondary" onClick={() => openCanvas({ title: "AP Copilot", type: "copilot" })}><Bot className="mr-2 h-4 w-4" /> Ask</Button>
                    </div>
                </div>
                <div className="flex-grow flex flex-col overflow-hidden bg-white border rounded-lg">
                    <Tabs defaultValue="review" className="h-full flex flex-col">
                        <TabsList className="m-2 flex-shrink-0">
                            <TabsTrigger value="review">Review & Resolve</TabsTrigger>
                            <TabsTrigger value="visualizer">Match Visualizer</TabsTrigger>
                            <TabsTrigger value="workflow">Workflow & Audit</TabsTrigger>
                        </TabsList>
                        <TabsContent value="review" className="flex-grow overflow-y-auto">
                            <ReviewResolveTab 
                                comparisonData={comparisonData} 
                                invoiceDbId={activeInvoice.id}
                                onDataUpdate={forceDataRefresh}
                                onApplySuggestion={(action: string) => {
                                    if (action === 'matched' || action === 'rejected') {
                                        handleStatusUpdate(action);
                                    }
                                }}
                            />
                        </TabsContent>
                        <TabsContent value="visualizer" className="flex-grow p-4 overflow-y-auto"><MatchVisualizerTab matchTrace={comparisonData?.match_trace || []} /></TabsContent>
                        <TabsContent value="workflow" className="flex-grow overflow-y-auto"><WorkflowAuditTab invoiceDbId={activeInvoice.id} onActionComplete={handleActionComplete} comparisonData={comparisonData} /></TabsContent>
                    </Tabs>
                </div>
            </>
        );
    };

    return (
        <div className="h-full max-h-[calc(100vh-8rem)] flex flex-col">
            <div className="flex-grow grid grid-cols-1 lg:grid-cols-10 gap-6">
                <div className={cn(
                    "lg:col-span-3 h-full rounded-lg flex flex-col bg-white border",
                    invoiceIdFromUrl && "hidden" // This hides the list when an invoice is open
                )}>
                    <InvoiceList 
                        selectedInvoiceId={activeInvoice?.invoice_id || null} 
                        onInvoiceSelect={handleInvoiceSelect}
                        refreshKey={queueRefreshKey}
                    />
                </div>
                <div className={cn(
                    "h-full flex flex-col space-y-4",
                    invoiceIdFromUrl ? "col-span-1 lg:col-span-10" : "col-span-1 lg:col-span-7"
                )}>
                    {renderMainContent()}
                </div>
            </div>
        </div>
    );
}

export default function ResolutionWorkbenchPage() {
    return (
        <Suspense fallback={<div className="flex h-full w-full items-center justify-center"><Loader2 className="w-10 h-10 animate-spin" /></div>}>
            <WorkbenchContent />
        </Suspense>
    );
} 