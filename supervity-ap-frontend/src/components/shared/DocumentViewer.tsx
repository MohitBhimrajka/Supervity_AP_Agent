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

// Configure PDF.js worker for Next.js
if (typeof window !== 'undefined') {
  // Use CDN worker which is more reliable for Next.js
  pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.js`;
}

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
    const loadDocument = async () => {
      if (filePath) {
        setIsLoading(true);
        setError(null);
        try {
          const blob = await getDocumentFile(filePath);
          const url = URL.createObjectURL(blob);
          setFileUrl(url);
        } catch (err) {
          setError("Could not load document.");
          setFileUrl(null);
        } finally {
          setIsLoading(false);
        }
      } else {
        setFileUrl(null);
        setError(null);
      }
    };
    if(isMounted) {
      loadDocument();
    }
    
    // Cleanup blob URL on component unmount or when doc changes
    return () => {
      if (fileUrl) {
        URL.revokeObjectURL(fileUrl);
      }
    };
  }, [filePath, isMounted]);

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