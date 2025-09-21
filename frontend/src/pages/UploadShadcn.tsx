import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Upload, Download, AlertCircle, CheckCircle2 } from 'lucide-react';
import { api } from '../api/client';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  Button,
  FileUpload,
  Alert,
  AlertDescription,
  Progress,
  useToast,
} from '@/components/ui';

export default function UploadShadcn() {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [uploading, setUploading] = useState(false);
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [uploadProgress, setUploadProgress] = useState(0);

  const handleFileSelect = (file: File) => {
    setUploadedFile(file);
    toast({
      title: "File selected",
      description: `${file.name} is ready for upload`,
    });
  };

  const handleFileRemove = () => {
    setUploadedFile(null);
    setUploadProgress(0);
  };

  const handleUpload = async () => {
    if (!uploadedFile) {
      toast({
        title: "No file selected",
        description: "Please select a file first",
        variant: "destructive",
      });
      return;
    }

    setUploading(true);
    setUploadProgress(0);

    // Simulate upload progress
    const progressInterval = setInterval(() => {
      setUploadProgress((prev) => {
        if (prev >= 90) {
          clearInterval(progressInterval);
          return 90;
        }
        return prev + 10;
      });
    }, 200);

    try {
      const result = await api.uploadFile(uploadedFile);

      clearInterval(progressInterval);
      setUploadProgress(100);

      if (result.status === 'completed') {
        toast({
          title: "Success!",
          description: "File uploaded and processed successfully",
        });
        setTimeout(() => {
          navigate(`/results/${result.session_id}`);
        }, 1000);
      } else {
        toast({
          title: "Upload failed",
          description: result.message || 'Unknown error occurred',
          variant: "destructive",
        });
        setUploadProgress(0);
      }
    } catch (error) {
      clearInterval(progressInterval);
      console.error('Upload error:', error);
      toast({
        title: "Upload failed",
        description: "Please try again later",
        variant: "destructive",
      });
      setUploadProgress(0);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8 p-6">
      {/* Header */}
      <div className="text-center">
        <h1 className="text-4xl font-bold tracking-tight">Upload Portfolio Data</h1>
        <p className="mt-4 text-lg text-muted-foreground">
          Upload your portfolio Excel file to start SALT calculation
        </p>
      </div>

      {/* Instructions Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertCircle className="h-5 w-5" />
            Before You Upload
          </CardTitle>
          <CardDescription>
            Please ensure your file meets the following requirements
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div className="space-y-2">
              <p className="flex items-start gap-2">
                <CheckCircle2 className="h-4 w-4 text-green-600 mt-0.5 flex-shrink-0" />
                Required columns: Investor Name, Investor Entity Type, Investor Tax State, Commitment Percentage, Distribution TX, Distribution NM, Distribution CO, and optional exemption columns
              </p>
              <p className="flex items-start gap-2">
                <CheckCircle2 className="h-4 w-4 text-green-600 mt-0.5 flex-shrink-0" />
                File size must be less than 10MB
              </p>
            </div>
            <div className="space-y-2">
              <p className="flex items-start gap-2">
                <CheckCircle2 className="h-4 w-4 text-green-600 mt-0.5 flex-shrink-0" />
                Supported formats: .xlsx, .xls
              </p>
              <div className="flex items-center gap-2">
                <Download className="h-4 w-4 text-primary" />
                <Button variant="link" className="h-auto p-0 text-sm" asChild>
                  <a href="/api/template" download>
                    Download standard template
                  </a>
                </Button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Upload Section */}
      <Card>
        <CardHeader>
          <CardTitle>Upload File</CardTitle>
          <CardDescription>
            Select your Excel file containing portfolio data
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <FileUpload
            onFileSelect={handleFileSelect}
            onFileRemove={handleFileRemove}
            selectedFile={uploadedFile}
            disabled={uploading}
          />

          {uploadedFile && (
            <div className="space-y-4">
              {/* Upload Progress */}
              {uploading && (
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>Processing file...</span>
                    <span>{uploadProgress}%</span>
                  </div>
                  <Progress value={uploadProgress} />
                </div>
              )}

              {/* Upload Button */}
              <div className="flex justify-center">
                <Button
                  onClick={handleUpload}
                  disabled={uploading}
                  size="lg"
                  className="px-8"
                >
                  {uploading ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-current mr-2" />
                      Processing...
                    </>
                  ) : (
                    <>
                      <Upload className="h-4 w-4 mr-2" />
                      Calculate SALT
                    </>
                  )}
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Processing Alert */}
      {uploading && (
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            Processing your file... This may take a few moments while we calculate SALT allocations.
          </AlertDescription>
        </Alert>
      )}
    </div>
  );
}