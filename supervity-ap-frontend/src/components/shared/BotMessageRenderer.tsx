"use client";

import ReactMarkdown from 'react-markdown';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../ui/Table';
import { Badge } from '../ui/Badge';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/Card';

interface BotMessageRendererProps {
  content: string;
  uiAction?: string;
  data?: unknown | null;
}

export const BotMessageRenderer = ({ content, uiAction, data }: BotMessageRendererProps) => {
  const renderData = () => {
    switch (uiAction) {
      case 'DISPLAY_JSON':
        return (
          <Card className="mt-4 bg-gray-50">
            <CardHeader><CardTitle className="text-base">Data Received</CardTitle></CardHeader>
            <CardContent>
              <pre className="bg-gray-200 p-3 rounded text-xs overflow-x-auto text-gray-800">
                {JSON.stringify(data, null, 2)}
              </pre>
            </CardContent>
          </Card>
        );

      case 'LOAD_DATA':
        if (Array.isArray(data) && data.length > 0 && typeof data[0] === 'object') {
          return (
            <Card className="mt-4 bg-gray-50">
              <CardContent className="pt-4">
                <div className="max-h-72 overflow-y-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        {Object.keys(data[0]).slice(0, 4).map((key) => (
                          <TableHead key={key} className="text-xs text-gray-600">
                            {key.replace(/_/g, ' ').toUpperCase()}
                          </TableHead>
                        ))}
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {data.map((item: Record<string, unknown>, index: number) => (
                        <TableRow key={index}>
                          {Object.entries(item).slice(0, 4).map(([key, value]) => (
                            <TableCell key={key} className="text-xs">
                              {key === 'status' ? (
                                <Badge variant="default" className="text-xs">
                                  {String(value).replace(/_/g, ' ')}
                                </Badge>
                              ) : (String(value) || 'N/A')}
                            </TableCell>
                          ))}
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              </CardContent>
            </Card>
          );
        }
        return null;

      case 'DISPLAY_MARKDOWN':
        return (
          <Card className="mt-4 bg-gray-50">
            <CardHeader><CardTitle className="text-base">Generated Draft</CardTitle></CardHeader>
            <CardContent>
              <div className="prose prose-sm max-w-none text-gray-800 bg-white p-4 rounded border">
                <ReactMarkdown>{(data as { draft_email?: string })?.draft_email || ''}</ReactMarkdown>
              </div>
            </CardContent>
          </Card>
        );
        
      default:
        return null;
    }
  };

  return (
    <div>
      <p className="text-gray-800">{content}</p>
      {renderData()}
    </div>
  );
}; 