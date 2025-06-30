"use client";

import { type JobResult } from "@/lib/api";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/Table";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import Link from "next/link";
import { CheckCircle, XCircle, Eye } from "lucide-react";

interface UploadStatusListProps {
  results: JobResult[];
}

export const UploadStatusList = ({ results }: UploadStatusListProps) => {
  if (!results || results.length === 0) {
    return <p className="text-center text-gray-medium">No processing results available.</p>;
  }

  return (
    <div className="mt-6 space-y-4">
      <h3 className="font-semibold text-lg">Processing Results</h3>
      <div className="border rounded-lg max-h-96 overflow-y-auto">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Status</TableHead>
              <TableHead>Filename</TableHead>
              <TableHead>Details</TableHead>
              <TableHead className="text-right">Action</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {results.map((result) => (
              <TableRow key={result.filename}>
                <TableCell>
                  <Badge variant={result.status === 'success' ? 'success' : 'destructive'}>
                    {result.status === 'success' ? <CheckCircle className="mr-2 h-4 w-4" /> : <XCircle className="mr-2 h-4 w-4" />}
                    {result.status}
                  </Badge>
                </TableCell>
                <TableCell className="font-medium">{result.filename}</TableCell>
                <TableCell className="text-sm text-gray-medium">{result.message}</TableCell>
                <TableCell className="text-right">
                  {result.status === 'success' && result.extracted_id && (
                    <Link href={`/resolution-workbench?invoiceId=${result.extracted_id}`}>
                      <Button variant="ghost" size="sm">
                        <Eye className="mr-2 h-4 w-4" /> View
                      </Button>
                    </Link>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}; 