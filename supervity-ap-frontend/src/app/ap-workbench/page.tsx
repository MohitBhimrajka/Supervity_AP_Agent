"use client";
import React, { useState, useEffect, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { InvoiceList } from '@/components/shared/InvoiceList';
import { type ComparisonData, getComparisonData, updateInvoiceStatus, type Invoice } from '@/lib/api';
import { useAppContext } from '@/lib/AppContext';
import { Loader2, FileSearch, CheckCircle, XCircle } from 'lucide-react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/Tabs';
import { Button } from '@/components/ui/Button';
import toast from 'react-hot-toast';
import { ReviewResolveTab } from '@/components/workbench/ReviewResolveTab';
import { MatchVisualizerTab } from '@/components/workbench/MatchVisualizerTab';
import { CollaborateAuditTab } from '@/components/workbench/CollaborateAuditTab';

function WorkbenchContent() {
    const { setCurrentInvoiceId } = useAppContext();
    const searchParams = useSearchParams();
    const initialInvoiceId = searchParams.get('invoiceId');

    const [selectedInvoice, setSelectedInvoice] = useState<Invoice | null>(null);
    const [comparisonData, setComparisonData] = useState<ComparisonData | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [refreshKey, setRefreshKey] = useState(0);
    const [dataRefreshTrigger, setDataRefreshTrigger] = useState(0);

    const forceDataRefresh = () => {
        setDataRefreshTrigger(prev => prev + 1);
    };

    const handleActionComplete = () => {
        setRefreshKey(prev => prev + 1);
        setSelectedInvoice(null);
        setComparisonData(null);
        setCurrentInvoiceId(null);
    };

    useEffect(() => {
        const fetchDataForInvoice = async () => {
            if (!selectedInvoice) {
                setComparisonData(null);
                setCurrentInvoiceId(null);
                return;
            }
            setIsLoading(true);
            setCurrentInvoiceId(selectedInvoice.invoice_id);
            try {
                const compData = await getComparisonData(selectedInvoice.id);
                setComparisonData(compData);
            } catch (error) {
                console.error("Failed to fetch invoice data", error);
                toast.error(`Failed to load data for ${selectedInvoice.invoice_id}`);
                setComparisonData(null);
            } finally {
                setIsLoading(false);
            }
        };

        fetchDataForInvoice();
    }, [selectedInvoice, setCurrentInvoiceId, dataRefreshTrigger]);

    const handleStatusUpdate = async (newStatus: 'approved_for_payment' | 'rejected') => {
        if (!selectedInvoice) return;
        setIsSubmitting(true);
        const reason = `Manually ${newStatus === 'approved_for_payment' ? 'Approved' : 'Rejected'} via Workbench`;
        
        try {
            await updateInvoiceStatus(selectedInvoice.invoice_id, { new_status: newStatus, reason });
            toast.success(`Invoice successfully ${newStatus === 'approved_for_payment' ? 'approved' : 'rejected'}.`);
            handleActionComplete();
        } catch (error) {
             toast.error(`Failed to update: ${error instanceof Error ? error.message : "Unknown error"}`);
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
      <div className="h-full max-h-[calc(100vh-8rem)] flex flex-col">
          <div className="flex-shrink-0">
              <h1 className="text-3xl font-bold text-black mb-6">AP Workbench</h1>
          </div>
          <div className="flex-grow grid grid-cols-1 lg:grid-cols-10 gap-6">
              <div className="lg:col-span-3 h-full rounded-lg flex flex-col bg-white border">
                  <InvoiceList 
                      selectedInvoiceId={selectedInvoice?.invoice_id || null} 
                      onInvoiceSelect={setSelectedInvoice}
                      refreshKey={refreshKey}
                      initialInvoiceId={initialInvoiceId}
                  />
              </div>

              <div className="lg:col-span-7 h-full flex flex-col space-y-4">
                  {isLoading ? (
                      <div className="h-full flex items-center justify-center text-gray-800"><Loader2 className="w-8 h-8 animate-spin" /> <span className="ml-3">Loading Invoice Data...</span></div>
                  ) : selectedInvoice ? (
                      <>
                          <div className="flex-shrink-0 bg-white p-4 rounded-lg border flex justify-between items-center">
                              <div>
                                  <h2 className="text-2xl font-bold text-black">{selectedInvoice.invoice_id}</h2>
                                  <p className="text-gray-500 font-medium">{selectedInvoice.vendor_name}</p>
                              </div>
                              <div className="flex items-center gap-4">
                                   <div className="text-right">
                                      <p className="text-sm text-gray-500">Total Amount</p>
                                      <p className="text-2xl font-bold text-black">${selectedInvoice.grand_total?.toFixed(2)}</p>
                                   </div>
                                   <div className="flex gap-2">
                                      <Button variant="success" onClick={() => handleStatusUpdate('approved_for_payment')} disabled={isSubmitting}>
                                          {isSubmitting ? <Loader2 className="mr-2 h-4 w-4 animate-spin"/> : <CheckCircle className="mr-2 h-4 w-4"/>} Approve
                                      </Button>
                                      <Button variant="destructive" onClick={() => handleStatusUpdate('rejected')} disabled={isSubmitting}>
                                          {isSubmitting ? <Loader2 className="mr-2 h-4 w-4 animate-spin"/> : <XCircle className="mr-2 h-4 w-4"/>} Reject
                                      </Button>
                                   </div>
                              </div>
                          </div>

                          <div className="flex-grow flex flex-col overflow-hidden bg-white border rounded-lg">
                              <Tabs defaultValue="review" className="h-full flex flex-col">
                                  <TabsList className="m-2">
                                      <TabsTrigger value="review">Review & Resolve</TabsTrigger>
                                      <TabsTrigger value="visualizer">Match Visualizer</TabsTrigger>
                                      <TabsTrigger value="collaborate">Collaborate & Audit</TabsTrigger>
                                  </TabsList>
                                  <TabsContent value="review" className="flex-grow overflow-y-auto">
                                      <ReviewResolveTab 
                                          comparisonData={comparisonData}
                                          invoiceDbId={selectedInvoice.id} 
                                          onDataUpdate={forceDataRefresh}
                                      />
                                  </TabsContent>
                                  <TabsContent value="visualizer" className="flex-grow p-4 overflow-y-auto">
                                      <MatchVisualizerTab matchTrace={comparisonData?.match_trace || []} />
                                  </TabsContent>
                                  <TabsContent value="collaborate" className="flex-grow p-4 overflow-y-auto">
                                     <CollaborateAuditTab 
                                         invoiceDbId={selectedInvoice.id} 
                                         invoiceId={selectedInvoice.invoice_id}
                                         vendorName={selectedInvoice.vendor_name || "the vendor"}
                                     />
                                  </TabsContent>
                              </Tabs>
                          </div>
                      </>
                  ) : (
                      <div className="p-4 h-full flex flex-col items-center justify-center text-center text-gray-800 bg-white border rounded-lg">
                          <FileSearch className="w-16 h-16 text-gray-600 mb-4" />
                          <h3 className="text-lg font-semibold text-black">Select an Invoice</h3>
                          <p className="text-gray-800 font-medium">Details and resolution tools will appear here once you select an invoice from the queue.</p>
                      </div>
                  )}
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