"use client";
import { type MatchTraceStep } from "@/lib/api";
import { MatchTrace } from "../shared/MatchTrace";

interface MatchVisualizerTabProps {
  matchTrace: MatchTraceStep[];
}

export const MatchVisualizerTab = ({ matchTrace }: MatchVisualizerTabProps) => {
  return (
    <div className="p-4 bg-white rounded-lg border">
      <h2 className="text-xl font-bold text-black mb-4">3-Way Match Trace</h2>
      <p className="text-sm text-gray-500 mb-6">
        This is a step-by-step log from the automated matching engine, showing exactly why this invoice was approved or flagged for review.
      </p>
      <MatchTrace trace={matchTrace} />
    </div>
  );
}; 