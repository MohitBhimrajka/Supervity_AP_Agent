"use client";

import { useState, useEffect } from "react";
import dynamic from "next/dynamic";
import { getDocumentFile } from "@/lib/api";
import { Loader2, AlertCircle, FileQuestion } from "lucide-react";
import { pdfjs } from 'react-pdf';
// Add imports for CSS, which is best practice for react-pdf
import 'react-pdf/dist/Page/AnnotationLayer.css';
import 'react-pdf/dist/Page/TextLayer.css';

// Dynamically import react-pdf components
const Document = dynamic(() => import("react-pdf").then((mod) => mod.Document), { ssr: false });
const Page = dynamic(() => import("react-pdf").then((mod) => mod.Page), { ssr: false });

// --- START FIX: This is the definitive fix for react-pdf v10+ ---
if (typeof window !== 'undefined') {
  // The path is now relative to the root of your site
  pdfjs.GlobalWorkerOptions.workerSrc = '/pdf.worker.min.mjs';
}
// --- END FIX ---

// Define a simpler prop type
interface DocumentViewerProps {
  filePath: string | null;
}

export const DocumentViewer = ({ filePath }: DocumentViewerProps) => {
  const [fileUrl, setFileUrl] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isMounted, setIsMounted] = useState(false);

  // Ensure component only renders on client side
  useEffect(() => {
    setIsMounted(true);
  }, []);

  useEffect(() => {
    // FIX 2: Correctly handle URL cleanup to prevent memory leaks
    let objectUrl: string | null = null;

    const loadDocument = async () => {
      if (!filePath) {
        setFileUrl(null);
        setError(null);
        return;
      }

      setIsLoading(true);
      setError(null);
      try {
        // getDocumentFile already returns a blob URL
        objectUrl = await getDocumentFile(filePath);
        setFileUrl(objectUrl);
      } catch {
        setError("Could not load document.");
        setFileUrl(null);
      } finally {
        setIsLoading(false);
      }
    };
    
    if(isMounted) {
      loadDocument();
    }
    
    // Cleanup function
    return () => {
      if (objectUrl) {
        URL.revokeObjectURL(objectUrl);
      }
    };
  }, [filePath, isMounted]); // FIX 3: Remove fileUrl from dependency array to prevent infinite loop

  if (!isMounted) return null; // Prevent rendering on server

  return (
    <div className="flex-grow overflow-y-auto bg-gray-200 p-4 flex justify-center">
      {isLoading && <div className="h-full flex items-center justify-center text-gray-800"><Loader2 className="w-8 h-8 animate-spin" /></div>}
      {error && <div className="h-full flex flex-col items-center justify-center text-pink-destructive"><AlertCircle className="w-8 h-8 mb-2" /><p className="font-medium">{error}</p></div>}
      {fileUrl && !isLoading && <Document file={fileUrl} loading={<Loader2 className="w-6 h-6 animate-spin" />} error={<p>Failed to load PDF.</p>}><Page pageNumber={1} renderTextLayer={false} renderAnnotationLayer={false} /></Document>}
      {!filePath && !isLoading && !error && (
        <div className="h-full flex flex-col items-center justify-center text-gray-500">
          <FileQuestion className="w-12 h-12 mb-2" />
          <p className="font-medium">Document not available</p>
        </div>
      )}
    </div>
  );
}; 