import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Upload, Download, AlertCircle, CheckCircle2, ArrowLeft } from 'lucide-react';
import { saltRulesApi } from '../api/saltRules';
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
import { Link } from 'react-router-dom';

export default function SaltRulesUpload() {
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
        description: "Please select a SALT rules matrix file first",
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
      const result = await saltRulesApi.upload(uploadedFile);

      clearInterval(progressInterval);
      setUploadProgress(100);

      if (result.status === 'validation_failed') {
        // Show validation errors with details
        const errors = result.validation_errors || [];
        const errorCount = errors.length;

        let errorMessage = result.message || 'File validation failed';
        if (errors.length > 0) {
          const maxErrorsToShow = 2;
          const errorList = errors.slice(0, maxErrorsToShow).map(err =>
            `• Row ${err.row || 'N/A'}: ${err.message || err.error || 'Unknown error'}`
          ).join('\n');
          errorMessage += `\n\n${errorList}`;

          if (errors.length > maxErrorsToShow) {
            errorMessage += `\n• ... and ${errors.length - maxErrorsToShow} more errors`;
          }
        }

        toast({
          title: "File validation failed",
          description: errorMessage,
          variant: "destructive",
        });

        console.error('Validation errors:', errors);
        setUploadProgress(0);
      } else {
        // File is valid and uploaded successfully
        toast({
          title: "Upload successful!",
          description: `File validated and uploaded. ${result.ruleCounts?.withholding || 0} withholding rules, ${result.ruleCounts?.composite || 0} composite rules processed.`,
        });

        // Navigate to the rule set details page after a short delay
        setTimeout(() => {
          navigate(`/salt-rules/${result.ruleSetId}`);
        }, 1000);
      }

    } catch (error: any) {
      clearInterval(progressInterval);
      console.error('Upload error:', error);

      const errorMessage = error.response?.data?.detail || error.response?.data?.message || error.message || 'Unknown error occurred';

      toast({
        title: "Upload failed",
        description: errorMessage,
        variant: "destructive",
      });
      setUploadProgress(0);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8 p-6">
      {/* Header with Back Navigation */}
      <div className="flex items-center space-x-4">
        <Link
          to="/salt-rules"
          className="inline-flex items-center text-sm text-gray-600 hover:text-gray-900"
        >
          <ArrowLeft className="h-4 w-4 mr-1" />
          Back to SALT Rules
        </Link>
      </div>

      <div className="text-center">
        <h1 className="text-4xl font-bold tracking-tight">Upload SALT Rules Matrix</h1>
        <p className="mt-4 text-lg text-muted-foreground">
          Upload Excel file containing SALT tax rules for validation and publishing
        </p>
      </div>

      {/* Instructions Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertCircle className="h-5 w-5" />
            SALT Rules Matrix Requirements
          </CardTitle>
          <CardDescription>
            Please ensure your SALT rules file meets the following requirements
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
            <div className="space-y-2">
              <p className="flex items-start gap-2">
                <CheckCircle2 className="h-4 w-4 text-green-600 mt-0.5 flex-shrink-0" />
                Excel format (.xlsx, .xls) with SALT rules data
              </p>
              <p className="flex items-start gap-2">
                <CheckCircle2 className="h-4 w-4 text-green-600 mt-0.5 flex-shrink-0" />
                Contains withholding and composite tax rules
              </p>
              <p className="flex items-start gap-2">
                <CheckCircle2 className="h-4 w-4 text-green-600 mt-0.5 flex-shrink-0" />
                File size must be less than 20MB
              </p>
            </div>
            <div className="space-y-2">
              <p className="flex items-start gap-2">
                <CheckCircle2 className="h-4 w-4 text-green-600 mt-0.5 flex-shrink-0" />
                State-based tax jurisdiction data
              </p>
              <p className="flex items-start gap-2">
                <CheckCircle2 className="h-4 w-4 text-green-600 mt-0.5 flex-shrink-0" />
                Valid tax rates and effective dates
              </p>
              <div className="flex items-center gap-2 mt-4">
                <Download className="h-4 w-4 text-primary" />
                <Button variant="link" className="h-auto p-0 text-sm" asChild>
                  <a href="/api/template/salt-rules" download>
                    Download SALT rules template
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
          <CardTitle>Upload SALT Rules File</CardTitle>
          <CardDescription>
            Select your Excel file containing the SALT tax rules matrix
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
              {/* File Details */}
              <div className="bg-gray-50 rounded-lg p-4">
                <h4 className="font-medium text-sm text-gray-900 mb-2">File Details</h4>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-gray-500">Filename:</span>
                    <p className="font-medium">{uploadedFile.name}</p>
                  </div>
                  <div>
                    <span className="text-gray-500">Size:</span>
                    <p className="font-medium">{(uploadedFile.size / 1024 / 1024).toFixed(2)} MB</p>
                  </div>
                </div>
              </div>

              {/* Upload Progress */}
              {uploading && (
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>Processing SALT rules file...</span>
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
                      Uploading & Validating...
                    </>
                  ) : (
                    <>
                      <Upload className="h-4 w-4 mr-2" />
                      Upload SALT Rules
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
            Processing your SALT rules file... This may take a few moments while we validate the tax rules matrix.
          </AlertDescription>
        </Alert>
      )}

    </div>
  );
}