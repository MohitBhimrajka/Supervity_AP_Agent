"use client";

import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { UploadCloud, File as FileIcon, X, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { uploadDocuments, type Job } from '@/lib/api'; // Import the real API function
import toast from 'react-hot-toast';

interface FileUploadProps {
  onUploadSuccess: (job: Job) => void;
}

export const FileUpload = ({ onUploadSuccess }: FileUploadProps) => {
  const [files, setFiles] = useState<File[]>([]);
  const [isUploading, setIsUploading] = useState(false);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    setFiles(prev => [...prev, ...acceptedFiles.filter(
      file => !prev.some(f => f.name === file.name)
    )]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({ 
    onDrop,
    accept: { 'application/pdf': ['.pdf'] }
  });

  const removeFile = (fileName: string) => {
    setFiles(prev => prev.filter(file => file.name !== fileName));
  };

  const handleUpload = async () => {
    if (files.length === 0 || isUploading) return;
    setIsUploading(true);
    try {
      const job = await uploadDocuments(files); // Using the real API
      toast.success(`Successfully uploaded ${files.length} document${files.length > 1 ? 's' : ''}!`);
      onUploadSuccess(job); // Pass the job to the parent component
      setFiles([]);
    } catch (error) {
      console.error("Upload failed", error);
      toast.error(`Upload failed: ${error instanceof Error ? error.message : 'Please try again.'}`);
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="w-full">
      <div
        {...getRootProps()}
        className={`p-10 border-2 border-dashed rounded-lg cursor-pointer transition-colors
          ${isDragActive ? 'border-blue-primary bg-blue-primary/10' : 'border-gray-light hover:border-blue-primary/50'}`}
      >
        <input {...getInputProps()} />
        <div className="flex flex-col items-center justify-center text-center">
          <UploadCloud className="w-12 h-12 text-gray-dark/80 mb-4" />
          <p className="font-semibold text-gray-900">
            {isDragActive ? "Drop the files here ..." : "Drag & drop files here, or click to select"}
          </p>
          <p className="text-sm text-gray-800 mt-1 font-medium">PDF documents only</p>
        </div>
      </div>

      {files.length > 0 && (
        <div className="mt-6">
          <h3 className="font-semibold text-lg mb-2">Files to Upload:</h3>
          <ul className="space-y-2">
            {files.map(file => (
              <li key={file.name} className="flex items-center justify-between p-2 bg-gray-100 rounded-md">
                <div className="flex items-center">
                  <FileIcon className="w-5 h-5 text-blue-primary mr-3" />
                  <span className="text-sm font-medium">{file.name}</span>
                </div>
                <button onClick={() => removeFile(file.name)} className="p-1 rounded-full hover:bg-pink-destructive/20">
                  <X className="w-4 h-4 text-pink-destructive" />
                </button>
              </li>
            ))}
          </ul>
          <Button onClick={handleUpload} disabled={isUploading} className="mt-4 w-full" size="lg">
            {isUploading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
            {isUploading ? 'Processing...' : `Process ${files.length} Document${files.length > 1 ? 's' : ''}`}
          </Button>
        </div>
      )}
    </div>
  );
} 