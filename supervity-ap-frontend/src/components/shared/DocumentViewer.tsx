"use client";

import { useState, useEffect } from "react";
import dynamic from "next/dynamic";
import { getDocumentFile, type Dossier } from "@/lib/api";
import { Button } from "../ui/Button";
import { Loader2, AlertCircle } from "lucide-react";

// Dynamically import react-pdf components to avoid SSR issues
const Document = dynamic(
  () => import("react-pdf").then((mod) => mod.Document),
  { ssr: false }
);

const Page = dynamic(
  () => import("react-pdf").then((mod) => mod.Page),
  { ssr: false }
);

// Configure PDF.js worker only on client side
if (typeof window !== 'undefined') {
  import("react-pdf").then((mod) => {
    mod.pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${mod.pdfjs.version}/build/pdf.worker.min.js`;
  });
}

type DocType = 'invoice' | 'grn' | 'po';

interface DocumentViewerProps {
  dossier: Dossier | null;
}

export const DocumentViewer = ({ dossier }: DocumentViewerProps) => {
  const [activeDocType, setActiveDocType] = useState<DocType>('invoice');
  const [fileUrl, setFileUrl] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isMounted, setIsMounted] = useState(false);

  // Ensure component only renders on client side
  useEffect(() => {
    setIsMounted(true);
  }, []);

  useEffect(() => {
    const loadDocument = async () => {
      if (!dossier) return;

      const doc = dossier.documents[activeDocType];
      if (doc && doc.file_path) {
        setIsLoading(true);
        setError(null);
        try {
          const url = await getDocumentFile(doc.file_path);
          setFileUrl(url);
        } catch (err) {
          console.error(err);
          setError(`Could not load ${activeDocType.toUpperCase()}.`);
          setFileUrl(null);
        } finally {
          setIsLoading(false);
        }
      } else {
        setFileUrl(null);
        setError(null);
      }
    };

    loadDocument();

    // Cleanup blob URL on component unmount or when doc changes
    return () => {
      if (fileUrl) {
        URL.revokeObjectURL(fileUrl);
      }
    };
  }, [dossier, activeDocType, fileUrl]);

  if (!dossier) {
    return (
              <div className="p-4 h-full flex items-center justify-center text-gray-800">
        <p>Select an invoice to view its documents.</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex-shrink-0 p-2 border-b flex gap-2">
        <Button
          size="sm"
          variant={activeDocType === 'invoice' ? 'primary' : 'secondary'}
          onClick={() => setActiveDocType('invoice')}
        >
          Invoice
        </Button>
        <Button
          size="sm"
          variant={activeDocType === 'grn' ? 'primary' : 'secondary'}
          onClick={() => setActiveDocType('grn')}
          disabled={!dossier.documents.grn?.file_path}
        >
          GRN
        </Button>
        <Button
          size="sm"
          variant={activeDocType === 'po' ? 'primary' : 'secondary'}
          onClick={() => setActiveDocType('po')}
          disabled={!dossier.documents.po?.file_path}
        >
          PO
        </Button>
      </div>
      {/* The scrolling container */}
      <div className="flex-grow overflow-y-auto bg-gray-200 p-4 flex justify-center">
        {isLoading && (
                          <div className="h-full flex items-center justify-center text-gray-800"><Loader2 className="w-8 h-8 animate-spin" /></div>
        )}
        {error && (
                          <div className="h-full flex flex-col items-center justify-center text-gray-800"><AlertCircle className="w-8 h-8 text-pink-destructive mb-2" /><p className="font-medium">{error}</p></div>
        )}
        {fileUrl && !isLoading && isMounted && (
          // The Document component from react-pdf
          <Document
            file={fileUrl}
            loading={<div className="flex items-center justify-center h-full"><Loader2 className="w-6 h-6 animate-spin"/></div>}
            error={<div className="flex items-center justify-center h-full text-pink-destructive">Failed to load PDF.</div>}
          >
            <Page pageNumber={1} />
          </Document>
        )}
        {!fileUrl && !isLoading && !error && (
                      <div className="h-full flex items-center justify-center text-gray-800"><p className="font-medium">Document not available.</p></div>
        )}
      </div>
    </div>
  );
}; 