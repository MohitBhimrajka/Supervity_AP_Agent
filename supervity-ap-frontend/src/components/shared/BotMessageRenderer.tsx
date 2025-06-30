"use client";

import ReactMarkdown from 'react-markdown';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';
import { Button } from '../ui/Button';
import { Eye } from 'lucide-react';
import { useAppContext } from '@/lib/AppContext';

interface BotMessageRendererProps {
  content: string;
  uiAction?: string;
  data?: unknown | null;
}

export const BotMessageRenderer = ({ content, uiAction, data }: BotMessageRendererProps) => {
  const { openCanvas } = useAppContext();

  const handleViewData = () => {
    if (!data) return;
    openCanvas({
      title: "Copilot Data Results",
      type: "data",
      data: data,
    });
  };

  const renderDataAction = () => {
    // These actions now open the side canvas
    if (uiAction === 'LOAD_DATA' || uiAction === 'DISPLAY_JSON') {
      return (
        <div className="mt-4">
          <Button variant="secondary" onClick={handleViewData}>
            <Eye className="mr-2 h-4 w-4" />
            View Data
          </Button>
        </div>
      );
    }
    
    // This action still renders inline as it's typically just text
    if (uiAction === 'DISPLAY_MARKDOWN') {
      return (
        <Card className="mt-4 bg-gray-50">
          <CardHeader><CardTitle className="text-base">Generated Draft</CardTitle></CardHeader>
          <CardContent>
            <div className="prose prose-sm max-w-none text-gray-dark bg-white p-4 rounded border">
              <ReactMarkdown>{(data as { draft_email?: string })?.draft_email || ''}</ReactMarkdown>
            </div>
          </CardContent>
        </Card>
      );
    }

    return null;
  };

  return (
    <div>
      <p className="text-gray-dark">{content}</p>
      {renderDataAction()}
    </div>
  );
}; 