"""File upload component with drag-and-drop functionality."""

import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FileText, AlertCircle, CheckCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';

export interface FileUploadProps {
  onFileSelect: (file: File) => void;
  onUploadComplete: (sessionId: string) => void;
  maxSize?: number; // in bytes
  acceptedTypes?: string[];
  disabled?: boolean;
}

export interface UploadProgress {
  status: 'idle' | 'uploading' | 'parsing' | 'validating' | 'saving' | 'completed' | 'error';
  progress: number;
  message?: string;
  sessionId?: string;
}

export const FileUpload: React.FC<FileUploadProps> = ({
  onFileSelect,
  onUploadComplete,
  maxSize = 10 * 1024 * 1024, // 10MB default
  acceptedTypes = ['.xlsx', '.xls'],
  disabled = false
}) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadProgress, setUploadProgress] = useState<UploadProgress>({
    status: 'idle',
    progress: 0
  });
  const [error, setError] = useState<string | null>(null);

  const validateFile = useCallback((file: File): string | null => {
    // Check file size
    if (file.size > maxSize) {
      const sizeMB = Math.round(maxSize / (1024 * 1024));
      return `File size exceeds ${sizeMB}MB limit. Current size: ${Math.round(file.size / (1024 * 1024) * 10) / 10}MB`;
    }

    // Check file type
    const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!acceptedTypes.includes(fileExtension)) {
      return `Invalid file type. Accepted types: ${acceptedTypes.join(', ')}`;
    }

    return null;
  }, [maxSize, acceptedTypes]);

  const handleUpload = async () => {
    if (!selectedFile) return;

    const validationError = validateFile(selectedFile);
    if (validationError) {
      setError(validationError);
      return;
    }

    setError(null);
    setUploadProgress({ status: 'uploading', progress: 5, message: 'Starting upload...' });

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);

      const response = await fetch('/api/upload', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Upload failed');
      }

      const result = await response.json();

      // Handle different response scenarios
      if (result.duplicate) {
        setUploadProgress({
          status: 'completed',
          progress: 100,
          message: 'File already processed',
          sessionId: result.session_id
        });
      } else if (result.status === 'FAILED_VALIDATION') {
        setUploadProgress({
          status: 'error',
          progress: 70,
          message: `Validation failed: ${result.error_count} errors found`
        });
        setError(`File contains ${result.error_count} validation errors that prevent processing`);
      } else if (result.status === 'COMPLETED') {
        setUploadProgress({
          status: 'completed',
          progress: 100,
          message: `Successfully processed ${result.distributions_created} distributions`,
          sessionId: result.session_id
        });
        onUploadComplete(result.session_id);
      } else {
        // Handle other status updates if needed
        setUploadProgress({
          status: result.status.toLowerCase() as UploadProgress['status'],
          progress: 90,
          message: result.message || 'Processing...'
        });
      }

    } catch (err) {
      console.error('Upload error:', err);
      setUploadProgress({
        status: 'error',
        progress: 0,
        message: 'Upload failed'
      });
      setError(err instanceof Error ? err.message : 'An unknown error occurred');
    }
  };

  const onDrop = useCallback((acceptedFiles: File[], rejectedFiles: any[]) => {
    setError(null);

    if (rejectedFiles.length > 0) {
      const rejection = rejectedFiles[0];
      if (rejection.errors[0]?.code === 'file-too-large') {
        const sizeMB = Math.round(maxSize / (1024 * 1024));
        setError(`File size exceeds ${sizeMB}MB limit`);
      } else if (rejection.errors[0]?.code === 'file-invalid-type') {
        setError(`Invalid file type. Accepted types: ${acceptedTypes.join(', ')}`);
      } else {
        setError('File rejected: ' + rejection.errors[0]?.message);
      }
      return;
    }

    if (acceptedFiles.length > 0) {
      const file = acceptedFiles[0];
      const validationError = validateFile(file);

      if (validationError) {
        setError(validationError);
        return;
      }

      setSelectedFile(file);
      setUploadProgress({ status: 'idle', progress: 0 });
      onFileSelect(file);
    }
  }, [maxSize, acceptedTypes, validateFile, onFileSelect]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': acceptedTypes,
      'application/vnd.ms-excel': acceptedTypes
    },
    maxSize,
    multiple: false,
    disabled: disabled || uploadProgress.status === 'uploading'
  });

  const resetUpload = () => {
    setSelectedFile(null);
    setUploadProgress({ status: 'idle', progress: 0 });
    setError(null);
  };

  const getStatusIcon = () => {
    switch (uploadProgress.status) {
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'error':
        return <AlertCircle className="h-5 w-5 text-red-500" />;
      default:
        return <FileText className="h-5 w-5 text-blue-500" />;
    }
  };

  const getStatusMessage = () => {
    if (uploadProgress.message) return uploadProgress.message;

    switch (uploadProgress.status) {
      case 'uploading':
        return 'Uploading file...';
      case 'parsing':
        return 'Parsing Excel file...';
      case 'validating':
        return 'Validating data...';
      case 'saving':
        return 'Saving to database...';
      case 'completed':
        return 'Upload completed successfully!';
      case 'error':
        return 'Upload failed';
      default:
        return '';
    }
  };

  return (
    <div className="w-full max-w-2xl mx-auto space-y-4">
      {/* Main Upload Area */}
      <Card>
        <CardContent className="p-6">
          <div
            {...getRootProps()}
            className={`
              border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors
              ${isDragActive
                ? 'border-blue-500 bg-blue-50 text-blue-700'
                : 'border-gray-300 hover:border-gray-400'
              }
              ${disabled || uploadProgress.status === 'uploading'
                ? 'opacity-50 cursor-not-allowed'
                : ''
              }
            `}
          >
            <input {...getInputProps()} />

            <div className="flex flex-col items-center space-y-4">
              <Upload className={`h-12 w-12 ${isDragActive ? 'text-blue-500' : 'text-gray-400'}`} />

              <div className="space-y-2">
                <p className="text-lg font-medium">
                  {isDragActive
                    ? 'Drop your Excel file here'
                    : 'Drag & drop your Excel file here'
                  }
                </p>
                <p className="text-sm text-gray-500">
                  or click to browse files
                </p>
                <p className="text-xs text-gray-400">
                  Supports: {acceptedTypes.join(', ')} • Max size: {Math.round(maxSize / (1024 * 1024))}MB
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Error Display */}
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Selected File Display */}
      {selectedFile && (
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                {getStatusIcon()}
                <div>
                  <p className="font-medium">{selectedFile.name}</p>
                  <p className="text-sm text-gray-500">
                    {Math.round(selectedFile.size / (1024 * 1024) * 10) / 10} MB
                  </p>
                </div>
              </div>

              <div className="flex items-center space-x-2">
                {uploadProgress.status === 'idle' && (
                  <>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={resetUpload}
                    >
                      Remove
                    </Button>
                    <Button
                      size="sm"
                      onClick={handleUpload}
                      disabled={disabled}
                    >
                      Upload
                    </Button>
                  </>
                )}

                {uploadProgress.status === 'completed' && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={resetUpload}
                  >
                    Upload Another
                  </Button>
                )}

                {uploadProgress.status === 'error' && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={resetUpload}
                  >
                    Try Again
                  </Button>
                )}
              </div>
            </div>

            {/* Progress Bar */}
            {uploadProgress.status !== 'idle' && uploadProgress.status !== 'error' && (
              <div className="mt-4 space-y-2">
                <Progress value={uploadProgress.progress} className="w-full" />
                <p className="text-sm text-gray-600">{getStatusMessage()}</p>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Template Download Link */}
      <div className="text-center">
        <Button variant="link" size="sm" asChild>
          <a href="/api/template" download>
            Download Excel Template
          </a>
        </Button>
      </div>
    </div>
  );
};