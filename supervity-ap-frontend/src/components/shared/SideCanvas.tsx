"use client";

import { useAppContext } from "@/lib/AppContext";
import { cn } from "@/lib/utils";
import { X } from "lucide-react";
import { Button } from "../ui/Button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../ui/Table';
import CopilotChatInterface from "./CopilotChatInterface";

// A generic renderer for the data inside the canvas
const DataRenderer = ({ data }: { data: unknown }) => {
    if (Array.isArray(data) && data.length > 0 && typeof data[0] === 'object') {
      const headers = Object.keys(data[0]);
      return (
        <div className="border rounded-lg overflow-hidden">
            <Table>
                <TableHeader>
                    <TableRow>
                        {headers.map(key => <TableHead key={key}>{key.replace(/_/g, ' ').toUpperCase()}</TableHead>)}
                    </TableRow>
                </TableHeader>
                <TableBody>
                    {data.map((row: Record<string, unknown>, rowIndex) => (
                        <TableRow key={rowIndex}>
                            {headers.map(header => <TableCell key={header}>{String(row[header] ?? 'N/A')}</TableCell>)}
                        </TableRow>
                    ))}
                </TableBody>
            </Table>
        </div>
      );
    }
    
    // Fallback for non-table data (e.g., JSON objects)
    return (
        <pre className="bg-gray-50 p-4 rounded text-xs overflow-x-auto text-gray-dark border">
            {JSON.stringify(data, null, 2)}
        </pre>
    );
}

export const SideCanvas = () => {
  const { isCanvasOpen, canvasContent, closeCanvas } = useAppContext();

  const renderContent = () => {
      if (!canvasContent) return null;
      
      switch (canvasContent.type) {
          case 'copilot':
              return <CopilotChatInterface />;
          case 'data':
              return (
                <div className="flex-grow p-6 overflow-y-auto">
                    {canvasContent?.data ? <DataRenderer data={canvasContent.data} /> : <p>No data to display.</p>}
                </div>
              );
          default:
              return null;
      }
  }

  return (
    <div
      className={cn(
        "fixed top-0 right-0 h-full bg-white shadow-2xl z-50 transition-transform duration-300 ease-in-out",
        "flex flex-col",
        isCanvasOpen ? "translate-x-0 w-full" : "translate-x-full w-0",
        canvasContent?.type === 'copilot' ? 'lg:w-[500px]' : 'lg:w-1/2'
      )}
    >
      <div className="flex justify-between items-center p-4 border-b shrink-0">
        <h2 className="text-xl font-bold text-black">{canvasContent?.title || 'Details'}</h2>
        <Button variant="ghost" size="sm" onClick={closeCanvas} className="p-1 rounded-full">
          <X className="w-5 h-5" />
        </Button>
      </div>
      
      {renderContent()}
    </div>
  );
}; 