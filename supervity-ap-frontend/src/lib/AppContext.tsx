"use client";
import React, { createContext, useContext, useState, ReactNode } from 'react';

// Define the shape of the data for the canvas
interface CanvasData {
  title: string;
  type: 'data' | 'copilot'; // Add type property
  data?: unknown; // Data is optional, not needed for copilot
}

interface AppContextType {
  currentInvoiceId: string | null;
  setCurrentInvoiceId: (id: string | null) => void;
  isCanvasOpen: boolean;
  canvasContent: CanvasData | null;
  openCanvas: (content: CanvasData) => void;
  closeCanvas: () => void;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export const AppProvider = ({ children }: { children: ReactNode }) => {
  const [currentInvoiceId, setCurrentInvoiceId] = useState<string | null>(null);
  const [isCanvasOpen, setIsCanvasOpen] = useState(false);
  const [canvasContent, setCanvasContent] = useState<CanvasData | null>(null);

  const openCanvas = (content: CanvasData) => {
    setCanvasContent(content);
    setIsCanvasOpen(true);
  };

  const closeCanvas = () => {
    setIsCanvasOpen(false);
    // Do not clear content immediately to allow for closing animation
  };

  return (
    <AppContext.Provider 
      value={{ 
        currentInvoiceId, 
        setCurrentInvoiceId,
        isCanvasOpen,
        canvasContent,
        openCanvas,
        closeCanvas
      }}
    >
      {children}
    </AppContext.Provider>
  );
};

export const useAppContext = () => {
  const context = useContext(AppContext);
  if (context === undefined) {
    throw new Error('useAppContext must be used within an AppProvider');
  }
  return context;
}; 