"use client";

import { useState } from "react";
import { type Job, syncSampleData } from "@/lib/api";
import { FileUpload } from "@/components/shared/FileUpload";
import { JobProgress } from "@/components/shared/JobProgress";
import { UploadStatusList } from "@/components/shared/UploadStatusList";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import toast from "react-hot-toast";
import { Database, Upload, Loader2 } from "lucide-react";

type ProcessingState = {
  job: Job | null;
  isLoading: boolean;
};

export default function DataCenterPage() {
  const [syncState, setSyncState] = useState<ProcessingState>({ job: null, isLoading: false });
  const [manualUploadState, setManualUploadState] = useState<ProcessingState>({ job: null, isLoading: false });

  const handleSyncClick = async () => {
    setSyncState({ job: null, isLoading: true });
    toast.loading("Starting sample data sync...", { id: "sync-toast" });
    try {
      const job = await syncSampleData();
      toast.success(`Sync job #${job.id} started!`, { id: "sync-toast" });
      setSyncState({ job, isLoading: true });
    } catch (error) {
      const message = error instanceof Error ? error.message : "An unknown error occurred.";
      toast.error(`Sync failed: ${message}`, { id: "sync-toast" });
      setSyncState({ job: null, isLoading: false });
    }
  };

  const handleManualUploadSuccess = (job: Job) => {
    setManualUploadState({ job, isLoading: true });
  };

  const handleSyncJobComplete = () => {
    toast.success(`Sync job completed!`);
    setSyncState(prev => ({ ...prev, isLoading: false }));
  };

  const handleManualJobComplete = () => {
    toast.success(`Upload job completed!`);
    setManualUploadState(prev => ({ ...prev, isLoading: false }));
  };
  
  const clearResults = (type: 'sync' | 'manual') => {
    if (type === 'sync') {
      setSyncState({ job: null, isLoading: false });
    } else {
      setManualUploadState({ job: null, isLoading: false });
    }
  };

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-start">

        {/* Left Card: Automated Sync */}
        <Card className="flex flex-col">
          <CardHeader>
            <div className="flex items-center gap-3">
              <Database className="w-8 h-8 text-purple-accent" />
              <div>
                <CardTitle>Automated Data Sync</CardTitle>
                <CardDescription>Simulate a sync from an external source.</CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="flex-grow overflow-hidden">
            {syncState.isLoading && syncState.job ? (
              <JobProgress key={syncState.job.id} initialJob={syncState.job} onComplete={handleSyncJobComplete} />
            ) : syncState.job && !syncState.isLoading ? (
              <div className="h-full flex flex-col">
                <div className="flex-grow overflow-y-auto">
                  <UploadStatusList results={syncState.job.summary || []} />
                </div>
                <Button variant="secondary" onClick={() => clearResults('sync')} className="mt-4 w-full flex-shrink-0">Start New Sync</Button>
              </div>
            ) : (
              <div className="text-center py-8">
                <p className="mb-4 text-gray-medium">Click to ingest all documents from the project&apos;s sample data directory.</p>
                <Button size="lg" onClick={handleSyncClick} disabled={syncState.isLoading}>
                  {syncState.isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                  Sync Sample Data
                </Button>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Right Card: Manual Upload */}
        <Card className="flex flex-col">
          <CardHeader>
            <div className="flex items-center gap-3">
              <Upload className="w-8 h-8 text-cyan-accent" />
              <div>
                <CardTitle>Manual Document Upload</CardTitle>
                <CardDescription>Upload one or more documents for processing.</CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="flex-grow overflow-hidden">
            {manualUploadState.isLoading && manualUploadState.job ? (
               <JobProgress key={manualUploadState.job.id} initialJob={manualUploadState.job} onComplete={handleManualJobComplete} />
            ) : manualUploadState.job && !manualUploadState.isLoading ? (
              <div className="h-full flex flex-col">
                <div className="flex-grow overflow-y-auto">
                  <UploadStatusList results={manualUploadState.job.summary || []} />
                </div>
                <Button variant="secondary" onClick={() => clearResults('manual')} className="mt-4 w-full flex-shrink-0">Upload More Files</Button>
              </div>
            ) : (
               <FileUpload onUploadSuccess={handleManualUploadSuccess} />
            )}
          </CardContent>
        </Card>

      </div>
    </div>
  );
} 