"use client";

import { useState, useEffect } from "react";
import { type Job, getJobStatus } from "@/lib/api";
import { Badge } from "../ui/Badge";
import { Loader2, CheckCircle, AlertTriangle } from "lucide-react";

interface JobProgressProps {
  initialJob: Job;
  onComplete: () => void; // A function to call when the job is done
}

export const JobProgress = ({ initialJob, onComplete }: JobProgressProps) => {
  const [job, setJob] = useState<Job>(initialJob);
  const progress = job.total_files > 0 ? (job.processed_files / job.total_files) * 100 : 0;

  useEffect(() => {
    if (job.status === "processing" || job.status === "matching") {
      const interval = setInterval(async () => {
        try {
          const updatedJob = await getJobStatus(job.id);
          setJob(updatedJob);
          if (updatedJob.status === "completed" || updatedJob.status === "failed") {
            clearInterval(interval);
            onComplete(); // Notify parent component
          }
        } catch (error) {
          console.error("Failed to poll job status:", error);
          clearInterval(interval);
        }
      }, 2000); // Poll every 2 seconds

      return () => clearInterval(interval);
    }
  }, [job.id, job.status, onComplete]);

  const getStatusInfo = () => {
    switch (job.status) {
        case "processing":
            return { icon: <Loader2 className="w-5 h-5 animate-spin" />, text: "Processing...", variant: "default" as const };
        case "matching":
            return { icon: <Loader2 className="w-5 h-5 animate-spin" />, text: "Matching...", variant: "default" as const };
        case "completed":
            return { icon: <CheckCircle className="w-5 h-5 text-green-success" />, text: "Completed", variant: "success" as const };
        case "failed":
            return { icon: <AlertTriangle className="w-5 h-5 text-pink-destructive" />, text: "Failed", variant: "destructive" as const };
        default:
            return { icon: <Loader2 className="w-5 h-5" />, text: "Pending...", variant: "default" as const };
    }
  };
  
  const { icon, text, variant } = getStatusInfo();

  return (
    <div className="p-4 border rounded-lg bg-gray-50">
      <div className="flex justify-between items-center mb-2">
        <h4 className="font-semibold">Job #{job.id}</h4>
        <Badge variant={variant} className="flex items-center gap-2">
            {icon}
            <span>{text}</span>
        </Badge>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2.5">
        <div
          className="bg-blue-primary h-2.5 rounded-full transition-all duration-500"
          style={{ width: `${progress}%` }}
        ></div>
      </div>
                  <p className="text-sm text-right mt-1 text-gray-800 font-medium">
        {job.processed_files} / {job.total_files} files
      </p>
    </div>
  );
};