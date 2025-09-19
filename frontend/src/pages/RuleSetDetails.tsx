import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  ArrowLeft,
  Eye,
  CheckCircle2,
  AlertCircle,
  XCircle,
  Download,
  Rocket,
  Clock,
  FileText
} from 'lucide-react';
import { saltRulesApi } from '../api/saltRules';
import type { RuleSet, ValidationResponse } from '../types/saltRules';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  Button,
  Alert,
  AlertDescription,
  Badge,
  useToast,
} from '@/components/ui';

export default function RuleSetDetails() {
  const { ruleSetId } = useParams<{ ruleSetId: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();

  const [ruleSet, setRuleSet] = useState<RuleSet | null>(null);
  const [validation, setValidation] = useState<ValidationResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [publishing, setPublishing] = useState(false);

  useEffect(() => {
    if (ruleSetId) {
      loadRuleSetData();
    }
  }, [ruleSetId]);

  const loadRuleSetData = async () => {
    if (!ruleSetId) return;

    try {
      setLoading(true);
      setError(null);

      // Load rule set details only (validation is done during upload)
      const ruleSetData = await saltRulesApi.getDetails(ruleSetId);
      setRuleSet(ruleSetData);
      setValidation(null); // No separate validation endpoint needed
    } catch (error: any) {
      console.error('Failed to load rule set data:', error);
      setError('Failed to load rule set details. Please try again.');
    } finally {
      setLoading(false);
    }
  };


  const handlePublish = async () => {
    if (!ruleSetId) return;

    setPublishing(true);
    try {
      await saltRulesApi.publish(ruleSetId, { confirmArchive: true });

      toast({
        title: "Rules published successfully!",
        description: "SALT rules are now active in the system",
      });

      // Reload data to show updated status
      await loadRuleSetData();

    } catch (error: any) {
      console.error('Failed to publish rules:', error);
      toast({
        title: "Publish failed",
        description: error.response?.data?.message || "Please try again later",
        variant: "destructive",
      });
    } finally {
      setPublishing(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'published':
        return 'bg-green-100 text-green-800';
      case 'validated':
        return 'bg-blue-100 text-blue-800';
      case 'uploaded':
        return 'bg-yellow-100 text-yellow-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'error':
        return <XCircle className="h-4 w-4 text-red-500" />;
      case 'warning':
        return <AlertCircle className="h-4 w-4 text-yellow-500" />;
      case 'info':
        return <CheckCircle2 className="h-4 w-4 text-blue-500" />;
      default:
        return <AlertCircle className="h-4 w-4 text-gray-500" />;
    }
  };

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto space-y-8 p-6">
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          <p className="mt-4 text-gray-500">Loading rule set details...</p>
        </div>
      </div>
    );
  }

  if (error || !ruleSet) {
    return (
      <div className="max-w-6xl mx-auto space-y-8 p-6">
        <Alert variant="destructive">
          <XCircle className="h-4 w-4" />
          <AlertDescription>
            {error || 'Rule set not found'}
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  const canPublish = ruleSet.status === 'validated';
  const hasValidationIssues = validation && validation.issues.some(issue => issue.severity === 'error');

  return (
    <div className="max-w-6xl mx-auto space-y-8 p-6">
      {/* Header with Navigation */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Link
            to="/salt-rules"
            className="inline-flex items-center text-sm text-gray-600 hover:text-gray-900"
          >
            <ArrowLeft className="h-4 w-4 mr-1" />
            Back to SALT Rules
          </Link>
        </div>

        <div className="flex items-center space-x-3">

          {canPublish && !hasValidationIssues && (
            <Button onClick={handlePublish} disabled={publishing}>
              {publishing ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-current mr-2" />
                  Publishing...
                </>
              ) : (
                <>
                  <Rocket className="h-4 w-4 mr-2" />
                  Publish Rules
                </>
              )}
            </Button>
          )}
        </div>
      </div>

      {/* Rule Set Overview */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5" />
                {ruleSet.filename}
              </CardTitle>
              <CardDescription>
                Rule Set ID: {ruleSet.ruleSetId}
              </CardDescription>
            </div>
            <Badge className={getStatusColor(ruleSet.status)}>
              {ruleSet.status.charAt(0).toUpperCase() + ruleSet.status.slice(1)}
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <h4 className="font-medium text-sm text-gray-900 mb-2">File Information</h4>
              <div className="space-y-1 text-sm">
                <p><span className="text-gray-500">Size:</span> {(ruleSet.fileSize / 1024 / 1024).toFixed(2)} MB</p>
                <p><span className="text-gray-500">Uploaded:</span> {formatDate(ruleSet.uploadedAt)}</p>
                {ruleSet.publishedAt && (
                  <p><span className="text-gray-500">Published:</span> {formatDate(ruleSet.publishedAt)}</p>
                )}
              </div>
            </div>

            <div>
              <h4 className="font-medium text-sm text-gray-900 mb-2">Rules Summary</h4>
              <div className="space-y-1 text-sm">
                <p><span className="text-gray-500">Withholding Rules:</span> {ruleSet.ruleCountWithholding}</p>
                <p><span className="text-gray-500">Composite Rules:</span> {ruleSet.ruleCountComposite}</p>
                <p><span className="text-gray-500">Total Rules:</span> {ruleSet.ruleCountWithholding + ruleSet.ruleCountComposite}</p>
              </div>
            </div>

            <div>
              <h4 className="font-medium text-sm text-gray-900 mb-2">Metadata</h4>
              <div className="space-y-1 text-sm">
                {ruleSet.version && <p><span className="text-gray-500">Version:</span> {ruleSet.version}</p>}
                {ruleSet.year && <p><span className="text-gray-500">Year:</span> {ruleSet.year}</p>}
                {ruleSet.quarter && <p><span className="text-gray-500">Quarter:</span> {ruleSet.quarter}</p>}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Validation Results */}
      {validation && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CheckCircle2 className="h-5 w-5" />
              Validation Results
            </CardTitle>
            <CardDescription>
              File validation completed in {validation.summary.processingTime}ms
            </CardDescription>
          </CardHeader>
          <CardContent>
            {/* Validation Summary */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
              <div className="text-center">
                <div className="text-2xl font-bold text-gray-900">{validation.summary.totalRules}</div>
                <div className="text-sm text-gray-500">Total Rules</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">{validation.summary.validRules}</div>
                <div className="text-sm text-gray-500">Valid Rules</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-red-600">{validation.summary.errorCount}</div>
                <div className="text-sm text-gray-500">Errors</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-yellow-600">{validation.summary.warningCount}</div>
                <div className="text-sm text-gray-500">Warnings</div>
              </div>
            </div>

            {/* Validation Issues */}
            {validation.issues.length > 0 && (
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <h4 className="font-medium">Validation Issues</h4>
                  <Button variant="outline" size="sm">
                    <Download className="h-4 w-4 mr-2" />
                    Export Issues
                  </Button>
                </div>

                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {validation.issues.slice(0, 10).map((issue, index) => (
                    <div key={index} className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg">
                      {getSeverityIcon(issue.severity)}
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900">{issue.message}</p>
                        {issue.rowNumber && (
                          <p className="text-xs text-gray-500">Row {issue.rowNumber}</p>
                        )}
                      </div>
                    </div>
                  ))}

                  {validation.issues.length > 10 && (
                    <p className="text-sm text-gray-500 text-center py-2">
                      And {validation.issues.length - 10} more issues...
                    </p>
                  )}
                </div>
              </div>
            )}

            {validation.issues.length === 0 && (
              <Alert>
                <CheckCircle2 className="h-4 w-4" />
                <AlertDescription>
                  All validation checks passed! The rules are ready for publishing.
                </AlertDescription>
              </Alert>
            )}
          </CardContent>
        </Card>
      )}

      {/* Status-specific Messages */}
      {ruleSet.status === 'uploaded' && (
        <Alert>
          <Clock className="h-4 w-4" />
          <AlertDescription>
            Validation is in progress. This page will automatically update when validation is complete.
          </AlertDescription>
        </Alert>
      )}

      {hasValidationIssues && (
        <Alert variant="destructive">
          <XCircle className="h-4 w-4" />
          <AlertDescription>
            This rule set has validation errors and cannot be published. Please fix the issues and re-upload.
          </AlertDescription>
        </Alert>
      )}

      {ruleSet.status === 'published' && (
        <Alert>
          <CheckCircle2 className="h-4 w-4" />
          <AlertDescription>
            These rules are currently published and active in the SALT calculation system.
          </AlertDescription>
        </Alert>
      )}
    </div>
  );
}