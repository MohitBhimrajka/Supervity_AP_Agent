"use client";
import { useState, useEffect } from 'react';
import { getLearnedHeuristics, type LearnedHeuristic } from '@/lib/api';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/Table';
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';

// A simple progress bar for confidence score
const ConfidenceBar = ({ score }: { score: number }) => (
  <div className="w-full bg-gray-200 rounded-full h-2.5">
    <div className="bg-blue-light h-2.5 rounded-full" style={{ width: `${score * 100}%` }}></div>
  </div>
);

export const LearnedHeuristicsTable = () => {
  const [heuristics, setHeuristics] = useState<LearnedHeuristic[]>([]);
  useEffect(() => {
    getLearnedHeuristics().then(setHeuristics);
  }, []);

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Vendor</TableHead>
          <TableHead>Exception Type</TableHead>
          <TableHead>Confidence</TableHead>
          <TableHead className="text-right">Action</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {heuristics.map(h => (
          <TableRow key={h.id}>
            <TableCell className="font-medium">{h.vendor_name}</TableCell>
            <TableCell><Badge variant="warning">{h.exception_type}</Badge></TableCell>
            <TableCell>
                <div className="flex items-center gap-2">
                    <ConfidenceBar score={h.confidence_score} />
                    <span>{(h.confidence_score * 100).toFixed(0)}%</span>
                </div>
            </TableCell>
            <TableCell className="text-right">
              <Button variant="ghost" size="sm" disabled={h.confidence_score < 0.9}>
                Promote to Rule
              </Button>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}; 