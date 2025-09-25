// Progress tracking component for upload and processing status.

import React from 'react';
import { CheckCircle, Circle, AlertCircle, Clock, Loader2 } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';

export interface ProcessingStep {
  id: string;
  label: string;
  description: string;
  status: 'pending' | 'in_progress' | 'completed' | 'error' | 'warning';
  progress?: number;
  message?: string;
  timestamp?: string;
}

export interface ProgressTrackerProps {
  sessionId?: string;
  currentStep: string;
  steps: ProcessingStep[];
  overallProgress: number;
  estimatedTimeRemaining?: number;
  showDetailedSteps?: boolean;
}

export const ProgressTracker: React.FC<ProgressTrackerProps> = ({
  sessionId,
  currentStep,
  steps,
  overallProgress,
  estimatedTimeRemaining,
  showDetailedSteps = true
}) => {
  const getStepIcon = (status: ProcessingStep['status'], isActive: boolean) => {
    const iconClass = `h-5 w-5 ${isActive ? 'animate-pulse' : ''}`;

    switch (status) {
      case 'completed':
        return <CheckCircle className={`${iconClass} text-green-500`} />;
      case 'in_progress':
        return <Loader2 className={`${iconClass} text-blue-500 animate-spin`} />;
      case 'error':
        return <AlertCircle className={`${iconClass} text-red-500`} />;
      case 'warning':
        return <AlertCircle className={`${iconClass} text-yellow-500`} />;
      case 'pending':
      default:
        return <Circle className={`${iconClass} text-gray-400`} />;
    }
  };

  const getStatusBadge = (status: ProcessingStep['status']) => {
    const variants = {
      completed: { variant: 'default' as const, label: 'Completed', className: 'bg-green-100 text-green-800' },
      in_progress: { variant: 'default' as const, label: 'In Progress', className: 'bg-blue-100 text-blue-800' },
      error: { variant: 'destructive' as const, label: 'Error', className: '' },
      warning: { variant: 'default' as const, label: 'Warning', className: 'bg-yellow-100 text-yellow-800' },
      pending: { variant: 'secondary' as const, label: 'Pending', className: '' }
    };

    const config = variants[status];
    return (
      <Badge variant={config.variant} className={config.className}>
        {config.label}
      </Badge>
    );
  };

  const formatTimeRemaining = (seconds: number): string => {
    if (seconds < 60) return `${Math.round(seconds)}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.round(seconds % 60);
    return `${minutes}m ${remainingSeconds}s`;
  };

  const getOverallStatus = (): { status: string; message: string; color: string } => {
    const hasError = steps.some(step => step.status === 'error');
    const hasWarning = steps.some(step => step.status === 'warning');
    const allCompleted = steps.every(step => step.status === 'completed');
    const hasInProgress = steps.some(step => step.status === 'in_progress');

    if (hasError) {
      return { status: 'Error', message: 'Processing failed', color: 'text-red-600' };
    }
    if (allCompleted) {
      return { status: 'Complete', message: 'Processing completed successfully', color: 'text-green-600' };
    }
    if (hasInProgress) {
      return { status: 'Processing', message: 'Processing in progress', color: 'text-blue-600' };
    }
    if (hasWarning) {
      return { status: 'Warning', message: 'Processing completed with warnings', color: 'text-yellow-600' };
    }
    return { status: 'Pending', message: 'Ready to start processing', color: 'text-gray-600' };
  };

  const overallStatus = getOverallStatus();

  return (
    <div className="w-full max-w-2xl mx-auto space-y-4">
      {/* Overall Progress */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-lg">Processing Status</CardTitle>
              {sessionId && (
                <p className="text-sm text-gray-500 mt-1">
                  Session: {sessionId.slice(0, 8)}...
                </p>
              )}
            </div>
            <div className="text-right">
              <div className={`text-sm font-medium ${overallStatus.color}`}>
                {overallStatus.status}
              </div>
              {estimatedTimeRemaining && estimatedTimeRemaining > 0 && (
                <div className="text-xs text-gray-500 flex items-center mt-1">
                  <Clock className="h-3 w-3 mr-1" />
                  {formatTimeRemaining(estimatedTimeRemaining)} remaining
                </div>
              )}
            </div>
          </div>
        </CardHeader>

        <CardContent className="space-y-4">
          {/* Overall Progress Bar */}
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">{overallStatus.message}</span>
              <span className="font-medium">{Math.round(overallProgress)}%</span>
            </div>
            <Progress value={overallProgress} className="w-full" />
          </div>

          {/* Detailed Steps */}
          {showDetailedSteps && (
            <div className="space-y-3 pt-2">
              <h4 className="text-sm font-medium text-gray-700">Processing Steps</h4>

              {steps.map((step, index) => {
                const isActive = step.id === currentStep;
                const isConnected = index < steps.length - 1;

                return (
                  <div key={step.id} className="relative">
                    {/* Step Content */}
                    <div className={`flex items-start space-x-3 p-3 rounded-lg transition-colors ${
                      isActive ? 'bg-blue-50 border border-blue-200' : 'bg-gray-50'
                    }`}>
                      {/* Icon */}
                      <div className="flex-shrink-0 mt-0.5">
                        {getStepIcon(step.status, isActive)}
                      </div>

                      {/* Content */}
                      <div className="flex-grow min-w-0">
                        <div className="flex items-center justify-between">
                          <h5 className="text-sm font-medium text-gray-900">
                            {step.label}
                          </h5>
                          {getStatusBadge(step.status)}
                        </div>

                        <p className="text-xs text-gray-600 mt-1">
                          {step.description}
                        </p>

                        {step.message && (
                          <p className="text-xs text-gray-700 mt-1 font-medium">
                            {step.message}
                          </p>
                        )}

                        {step.timestamp && (
                          <p className="text-xs text-gray-500 mt-1">
                            {new Date(step.timestamp).toLocaleTimeString()}
                          </p>
                        )}

                        {/* Step Progress Bar */}
                        {step.progress !== undefined && step.progress > 0 && step.status === 'in_progress' && (
                          <div className="mt-2">
                            <Progress value={step.progress} className="w-full h-1" />
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Connector Line */}
                    {isConnected && (
                      <div className="absolute left-6 top-12 w-px h-4 bg-gray-300" />
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

// Predefined step configurations for common workflows
export const createUploadSteps = (): ProcessingStep[] => [
  {
    id: 'upload',
    label: 'File Upload',
    description: 'Uploading Excel file to server',
    status: 'pending'
  },
  {
    id: 'parsing',
    label: 'File Parsing',
    description: 'Reading and parsing Excel data',
    status: 'pending'
  },
  {
    id: 'validation',
    label: 'Data Validation',
    description: 'Validating investor and distribution data',
    status: 'pending'
  },
  {
    id: 'saving',
    label: 'Data Processing',
    description: 'Saving processed data to database',
    status: 'pending'
  },
  {
    id: 'completed',
    label: 'Processing Complete',
    description: 'File processed successfully',
    status: 'pending'
  }
];

export const updateStepStatus = (
  steps: ProcessingStep[],
  stepId: string,
  status: ProcessingStep['status'],
  message?: string,
  progress?: number
): ProcessingStep[] => {
  return steps.map(step => {
    if (step.id === stepId) {
      return {
        ...step,
        status,
        message,
        progress,
        timestamp: new Date().toISOString()
      };
    }
    return step;
  });
};