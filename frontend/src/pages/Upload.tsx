import React, { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDropzone } from 'react-dropzone';
import { toast } from 'react-hot-toast';
import { CloudArrowUpIcon, DocumentIcon, XMarkIcon } from '@heroicons/react/24/outline';
import { api } from '../api/client';

export default function Upload() {
  const navigate = useNavigate();
  const [uploading, setUploading] = useState(false);
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const file = acceptedFiles[0];
    if (file) {
      // Validate file type
      if (!file.name.endsWith('.xlsx') && !file.name.endsWith('.xls')) {
        toast.error('Please upload only Excel files (.xlsx or .xls)');
        return;
      }

      // Validate file size (10MB limit)
      if (file.size > 10 * 1024 * 1024) {
        toast.error('File size must be less than 10MB');
        return;
      }

      setUploadedFile(file);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.ms-excel': ['.xls'],
    },
    multiple: false,
  });

  const handleUpload = async () => {
    if (!uploadedFile) {
      toast.error('Please select a file first');
      return;
    }

    setUploading(true);
    
    try {
      const result = await api.uploadFile(uploadedFile);
      
      if (result.status === 'completed') {
        toast.success('File uploaded and processed successfully!');
        navigate(`/results/${result.session_id}`);
      } else {
        toast.error(result.message || 'Upload failed');
      }
    } catch (error) {
      console.error('Upload error:', error);
      toast.error('Upload failed. Please try again.');
    } finally {
      setUploading(false);
    }
  };

  const removeFile = () => {
    setUploadedFile(null);
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="max-w-3xl mx-auto space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Upload Portfolio Data</h1>
        <p className="mt-2 text-gray-600">
          Upload your portfolio Excel file to start SALT calculation
        </p>
      </div>

      {/* Instructions */}
      <div className="card p-6">
        <h2 className="text-lg font-medium text-gray-900 mb-4">Before You Upload</h2>
        <div className="space-y-3 text-sm text-gray-600">
          <p>• Make sure your Excel file contains the required columns: Company Name, State, Revenue, LP Name, Ownership Percentage</p>
          <p>• File size must be less than 10MB</p>
          <p>• Supported formats: .xlsx, .xls</p>
          <p>• Need a template? 
            <a 
              href="/api/template" 
              download 
              className="text-primary-600 hover:text-primary-700 ml-1"
            >
              Download the standard template
            </a>
          </p>
        </div>
      </div>

      {/* Upload Area */}
      <div className="card p-8">
        {!uploadedFile ? (
          <div
            {...getRootProps()}
            className={`border-2 border-dashed border-gray-300 rounded-lg p-12 text-center cursor-pointer transition-colors ${
              isDragActive ? 'border-primary-400 bg-primary-50' : 'hover:border-gray-400'
            }`}
          >
            <input {...getInputProps()} />
            <CloudArrowUpIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            {isDragActive ? (
              <p className="text-primary-600 font-medium">Drop your Excel file here</p>
            ) : (
              <>
                <p className="text-lg font-medium text-gray-900 mb-2">
                  Drag and drop your Excel file here
                </p>
                <p className="text-gray-500">
                  or <span className="text-primary-600">click to browse</span>
                </p>
              </>
            )}
          </div>
        ) : (
          <div className="space-y-6">
            {/* Uploaded File */}
            <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
              <div className="flex items-center">
                <DocumentIcon className="h-8 w-8 text-green-600 mr-3" />
                <div>
                  <p className="font-medium text-gray-900">{uploadedFile.name}</p>
                  <p className="text-sm text-gray-500">{formatFileSize(uploadedFile.size)}</p>
                </div>
              </div>
              <button
                onClick={removeFile}
                className="text-gray-400 hover:text-red-500 transition-colors"
                disabled={uploading}
              >
                <XMarkIcon className="h-5 w-5" />
              </button>
            </div>

            {/* Upload Button */}
            <div className="flex justify-center">
              <button
                onClick={handleUpload}
                disabled={uploading}
                className="btn-primary px-8 py-3 text-lg"
              >
                {uploading ? (
                  <>
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                    Processing...
                  </>
                ) : (
                  <>
                    <CloudArrowUpIcon className="h-5 w-5 mr-2" />
                    Calculate SALT
                  </>
                )}
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Processing Info */}
      {uploading && (
        <div className="card p-6 bg-blue-50 border-blue-200">
          <div className="flex items-center">
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600 mr-3"></div>
            <div>
              <p className="font-medium text-blue-900">Processing your file...</p>
              <p className="text-sm text-blue-700 mt-1">
                This may take a few moments while we calculate SALT allocations.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}