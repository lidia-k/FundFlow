"""Error handling component for application-wide error display."""

import React from 'react';
import { AlertCircle, XCircle, AlertTriangle, Info, RefreshCw, Home, Download } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';

export interface ErrorInfo {
  code?: string;
  message: string;
  details?: string;
  timestamp?: string;
  sessionId?: string;
  context?: Record<string, any>;
}

export interface ErrorDisplayProps {
  error: ErrorInfo;
  type?: 'error' | 'warning' | 'info';
  variant?: 'inline' | 'page' | 'modal';
  showRetry?: boolean;
  showHome?: boolean;
  showDownloadErrors?: boolean;
  onRetry?: () => void;
  onHome?: () => void;
  onDownloadErrors?: () => void;
  onDismiss?: () => void;
  className?: string;
}

export const ErrorDisplay: React.FC<ErrorDisplayProps> = ({
  error,
  type = 'error',
  variant = 'inline',
  showRetry = false,
  showHome = false,
  showDownloadErrors = false,
  onRetry,
  onHome,
  onDownloadErrors,
  onDismiss,
  className = ''
}) => {
  const getIcon = () => {
    const iconClass = "h-5 w-5";

    switch (type) {
      case 'warning':
        return <AlertTriangle className={`${iconClass} text-yellow-500`} />;
      case 'info':
        return <Info className={`${iconClass} text-blue-500`} />;
      case 'error':
      default:
        return <XCircle className={`${iconClass} text-red-500`} />;
    }
  };

  const getTitle = () => {
    switch (type) {
      case 'warning':
        return 'Warning';
      case 'info':
        return 'Information';
      case 'error':
      default:
        return 'Error';
    }
  };

  const getVariantClasses = () => {
    switch (variant) {
      case 'page':
        return 'min-h-[400px] flex items-center justify-center';
      case 'modal':
        return 'max-w-md mx-auto';
      case 'inline':
      default:
        return '';
    }
  };

  const formatTimestamp = (timestamp?: string) => {
    if (!timestamp) return '';
    return new Date(timestamp).toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  // Inline variant - simple alert
  if (variant === 'inline') {
    return (
      <Alert variant={type === 'error' ? 'destructive' : 'default'} className={className}>
        {getIcon()}
        <AlertDescription className="flex-grow">
          <div className="flex items-start justify-between">
            <div className="flex-grow">
              <p className="font-medium">{error.message}</p>
              {error.details && (
                <p className="text-sm text-gray-600 mt-1">{error.details}</p>
              )}
              {error.code && (
                <Badge variant="outline" className="mt-2 text-xs">
                  Code: {error.code}
                </Badge>
              )}
            </div>
            {onDismiss && (
              <Button
                variant="ghost"
                size="sm"
                onClick={onDismiss}
                className="ml-2 h-6 w-6 p-0"
              >
                <XCircle className="h-4 w-4" />
              </Button>
            )}
          </div>
        </AlertDescription>
      </Alert>
    );
  }

  // Page and Modal variants - full card display
  return (
    <div className={`${getVariantClasses()} ${className}`}>
      <Card className="w-full max-w-lg">
        <CardHeader className="text-center">
          <div className="flex justify-center mb-4">
            <div className="p-3 rounded-full bg-gray-100">
              {getIcon()}
            </div>
          </div>
          <CardTitle className="text-lg">{getTitle()}</CardTitle>
        </CardHeader>

        <CardContent className="space-y-4">
          {/* Main Error Message */}
          <div className="text-center">
            <p className="text-gray-900 font-medium">{error.message}</p>
            {error.details && (
              <p className="text-gray-600 text-sm mt-2">{error.details}</p>
            )}
          </div>

          {/* Error Metadata */}
          {(error.code || error.timestamp || error.sessionId) && (
            <div className="bg-gray-50 rounded-lg p-3 space-y-2">
              {error.code && (
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Error Code:</span>
                  <code className="text-gray-900 font-mono">{error.code}</code>
                </div>
              )}

              {error.sessionId && (
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Session ID:</span>
                  <code className="text-gray-900 font-mono">{error.sessionId.slice(0, 8)}...</code>
                </div>
              )}

              {error.timestamp && (
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Time:</span>
                  <span className="text-gray-900">{formatTimestamp(error.timestamp)}</span>
                </div>
              )}
            </div>
          )}

          {/* Context Information */}
          {error.context && Object.keys(error.context).length > 0 && (
            <div className="bg-gray-50 rounded-lg p-3">
              <h4 className="text-sm font-medium text-gray-700 mb-2">Additional Information</h4>
              <div className="space-y-1">
                {Object.entries(error.context).map(([key, value]) => (
                  <div key={key} className="flex justify-between text-sm">
                    <span className="text-gray-600 capitalize">{key.replace(/_/g, ' ')}:</span>
                    <span className="text-gray-900">
                      {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex flex-col sm:flex-row gap-2 pt-2">
            {showRetry && onRetry && (
              <Button
                onClick={onRetry}
                className="flex-1"
              >
                <RefreshCw className="h-4 w-4 mr-2" />
                Try Again
              </Button>
            )}

            {showDownloadErrors && onDownloadErrors && (
              <Button
                variant="outline"
                onClick={onDownloadErrors}
                className="flex-1"
              >
                <Download className="h-4 w-4 mr-2" />
                Download Errors
              </Button>
            )}

            {showHome && onHome && (
              <Button
                variant="outline"
                onClick={onHome}
                className="flex-1"
              >
                <Home className="h-4 w-4 mr-2" />
                Go Home
              </Button>
            )}

            {onDismiss && (
              <Button
                variant="ghost"
                onClick={onDismiss}
                className="flex-1"
              >
                Dismiss
              </Button>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

// Predefined error configurations for common scenarios
export const createFileUploadError = (message: string, details?: string): ErrorInfo => ({
  code: 'UPLOAD_ERROR',
  message,
  details,
  timestamp: new Date().toISOString()
});

export const createValidationError = (sessionId: string, errorCount: number): ErrorInfo => ({
  code: 'VALIDATION_ERROR',
  message: `File contains ${errorCount} validation errors`,
  details: 'Please review the errors and upload a corrected file.',
  sessionId,
  timestamp: new Date().toISOString(),
  context: {
    error_count: errorCount,
    action_required: 'Fix validation errors and re-upload'
  }
});

export const createProcessingError = (sessionId: string, stage: string): ErrorInfo => ({
  code: 'PROCESSING_ERROR',
  message: `Processing failed during ${stage}`,
  details: 'An unexpected error occurred while processing your file.',
  sessionId,
  timestamp: new Date().toISOString(),
  context: {
    processing_stage: stage,
    action_required: 'Try uploading the file again or contact support'
  }
});

export const createNetworkError = (): ErrorInfo => ({
  code: 'NETWORK_ERROR',
  message: 'Network connection failed',
  details: 'Please check your internet connection and try again.',
  timestamp: new Date().toISOString(),
  context: {
    action_required: 'Check network connection and retry'
  }
});

export const createFileFormatError = (filename: string, expectedFormats: string[]): ErrorInfo => ({
  code: 'FORMAT_ERROR',
  message: 'Invalid file format',
  details: `File "${filename}" is not in a supported format. Expected: ${expectedFormats.join(', ')}`,
  timestamp: new Date().toISOString(),
  context: {
    filename,
    expected_formats: expectedFormats.join(', '),
    action_required: 'Upload a file in the correct format'
  }
});

export const createFileSizeError = (filename: string, size: number, maxSize: number): ErrorInfo => ({
  code: 'SIZE_ERROR',
  message: 'File size exceeds limit',
  details: `File "${filename}" (${Math.round(size / (1024 * 1024) * 10) / 10}MB) exceeds the ${Math.round(maxSize / (1024 * 1024))}MB limit.`,
  timestamp: new Date().toISOString(),
  context: {
    filename,
    file_size_mb: Math.round(size / (1024 * 1024) * 10) / 10,
    max_size_mb: Math.round(maxSize / (1024 * 1024)),
    action_required: 'Upload a smaller file or compress the data'
  }
});

// Error boundary component for catching React errors
export class ErrorBoundary extends React.Component<
  { children: React.ReactNode; fallback?: React.ComponentType<{error: Error}> },
  { hasError: boolean; error?: Error }
> {
  constructor(props: any) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Error boundary caught an error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError && this.state.error) {
      if (this.props.fallback) {
        const FallbackComponent = this.props.fallback;
        return <FallbackComponent error={this.state.error} />;
      }

      return (
        <ErrorDisplay
          error={{
            code: 'REACT_ERROR',
            message: 'An unexpected error occurred',
            details: this.state.error.message,
            timestamp: new Date().toISOString()
          }}
          variant="page"
          showHome={true}
          onHome={() => window.location.reload()}
        />
      );
    }

    return this.props.children;
  }
}