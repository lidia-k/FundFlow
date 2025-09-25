// Results display component with data grid for distribution results.

import React, { useState, useMemo } from 'react';
import { Download, Filter, Search, AlertTriangle, CheckCircle, XCircle } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';

export interface DistributionResult {
  id: string;
  investor_name: string;
  entity_type: string;
  tax_state: string;
  fund_code: string;
  period: string;
  jurisdiction: string;
  amount: number;
  composite_exemption: boolean;
  withholding_exemption: boolean;
  created_at: string;
}

export interface ValidationError {
  row_number: number;
  column_name: string;
  error_code: string;
  error_message: string;
  severity: 'ERROR' | 'WARNING';
  field_value?: string;
  created_at: string;
}

export interface SessionSummary {
  session_id: string;
  status: string;
  total_rows: number;
  valid_rows: number;
  created_at: string;
  completed_at?: string;
}

export interface ResultsData {
  session: SessionSummary;
  distributions: {
    data: DistributionResult[];
    count: number;
    summary: {
      total_amount: number;
      total_composite_exempt: number;
      total_withholding_exempt: number;
      exemption_summary: {
        composite_exempt_count: number;
        withholding_exempt_count: number;
        both_exempt_count: number;
        no_exemption_count: number;
      };
    };
  };
  validation_errors: {
    data: ValidationError[];
    summary: {
      total_errors: number;
      error_count: number;
      warning_count: number;
    };
  };
}

export interface ResultsDisplayProps {
  sessionId: string;
  data: ResultsData;
  isLoading?: boolean;
  onDownload: (sessionId: string, format: 'csv' | 'excel') => void;
  onDownloadErrors: (sessionId: string) => void;
  showPreviewOnly?: boolean;
  previewLimit?: number;
}

export const ResultsDisplay: React.FC<ResultsDisplayProps> = ({
  sessionId,
  data,
  isLoading = false,
  onDownload,
  onDownloadErrors,
  showPreviewOnly = false,
  previewLimit = 100
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [filterJurisdiction, setFilterJurisdiction] = useState<string>('all');
  const [activeTab, setActiveTab] = useState<'distributions' | 'errors'>('distributions');

  // Filter and search distributions
  const filteredDistributions = useMemo(() => {
    let filtered = data.distributions.data;

    // Apply search filter
    if (searchTerm) {
      const search = searchTerm.toLowerCase();
      filtered = filtered.filter(dist =>
        dist.investor_name.toLowerCase().includes(search) ||
        dist.entity_type.toLowerCase().includes(search) ||
        dist.tax_state.toLowerCase().includes(search) ||
        dist.fund_code.toLowerCase().includes(search)
      );
    }

    // Apply jurisdiction filter
    if (filterJurisdiction !== 'all') {
      filtered = filtered.filter(dist => dist.jurisdiction === filterJurisdiction);
    }

    // Apply preview limit if enabled
    if (showPreviewOnly) {
      filtered = filtered.slice(0, previewLimit);
    }

    return filtered;
  }, [data.distributions.data, searchTerm, filterJurisdiction, showPreviewOnly, previewLimit]);

  // Get unique jurisdictions for filter
  const jurisdictions = useMemo(() => {
    const unique = [...new Set(data.distributions.data.map(d => d.jurisdiction))];
    return unique.sort();
  }, [data.distributions.data]);

  const formatCurrency = (amount: number): string => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getStatusIcon = () => {
    switch (data.session.status) {
      case 'COMPLETED':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'FAILED_VALIDATION':
        return <XCircle className="h-5 w-5 text-red-500" />;
      case 'FAILED_SAVING':
        return <XCircle className="h-5 w-5 text-red-500" />;
      default:
        return <AlertTriangle className="h-5 w-5 text-yellow-500" />;
    }
  };

  if (isLoading) {
    return (
      <div className="w-full max-w-6xl mx-auto space-y-4">
        <Card>
          <CardContent className="p-8 text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading results...</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="w-full max-w-6xl mx-auto space-y-6">
      {/* Session Summary */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              {getStatusIcon()}
              <div>
                <CardTitle>Processing Results</CardTitle>
                <p className="text-sm text-gray-600 mt-1">
                  Session: {sessionId.slice(0, 8)}... •
                  Processed: {formatDate(data.session.created_at)}
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => onDownload(sessionId, 'csv')}
                disabled={data.distributions.count === 0}
              >
                <Download className="h-4 w-4 mr-2" />
                Download CSV
              </Button>
              {data.validation_errors.data.length > 0 && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onDownloadErrors(sessionId)}
                >
                  <Download className="h-4 w-4 mr-2" />
                  Download Errors
                </Button>
              )}
            </div>
          </div>
        </CardHeader>

        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <div className="text-2xl font-bold text-blue-600">{data.session.total_rows}</div>
              <div className="text-sm text-gray-600">Total Rows</div>
            </div>
            <div className="text-center p-4 bg-green-50 rounded-lg">
              <div className="text-2xl font-bold text-green-600">{data.session.valid_rows}</div>
              <div className="text-sm text-gray-600">Valid Rows</div>
            </div>
            <div className="text-center p-4 bg-purple-50 rounded-lg">
              <div className="text-2xl font-bold text-purple-600">{data.distributions.count}</div>
              <div className="text-sm text-gray-600">Distributions</div>
            </div>
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <div className="text-2xl font-bold text-gray-600">
                {formatCurrency(data.distributions.summary.total_amount)}
              </div>
              <div className="text-sm text-gray-600">Total Amount</div>
            </div>
          </div>

          {/* Exemption Summary */}
          {data.distributions.summary.exemption_summary && (
            <div className="mt-4 p-4 bg-gray-50 rounded-lg">
              <h4 className="text-sm font-medium text-gray-700 mb-3">Exemption Summary</h4>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                <div>
                  <span className="text-gray-600">Composite Exempt:</span>
                  <span className="ml-2 font-medium">
                    {data.distributions.summary.exemption_summary.composite_exempt_count}
                  </span>
                </div>
                <div>
                  <span className="text-gray-600">Withholding Exempt:</span>
                  <span className="ml-2 font-medium">
                    {data.distributions.summary.exemption_summary.withholding_exempt_count}
                  </span>
                </div>
                <div>
                  <span className="text-gray-600">Both Exempt:</span>
                  <span className="ml-2 font-medium">
                    {data.distributions.summary.exemption_summary.both_exempt_count}
                  </span>
                </div>
                <div>
                  <span className="text-gray-600">No Exemption:</span>
                  <span className="ml-2 font-medium">
                    {data.distributions.summary.exemption_summary.no_exemption_count}
                  </span>
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Validation Errors Alert */}
      {data.validation_errors.data.length > 0 && (
        <Alert variant={data.validation_errors.summary.error_count > 0 ? "destructive" : "default"}>
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>
            Found {data.validation_errors.summary.total_errors} validation issues:
            {' '}
            {data.validation_errors.summary.error_count} errors,
            {' '}
            {data.validation_errors.summary.warning_count} warnings.
            {data.validation_errors.summary.error_count > 0 &&
              " Errors prevent data processing."}
          </AlertDescription>
        </Alert>
      )}

      {/* Tab Navigation */}
      <div className="flex space-x-1 border-b">
        <button
          className={`px-4 py-2 text-sm font-medium rounded-t-lg ${
            activeTab === 'distributions'
              ? 'bg-white border-b-2 border-blue-500 text-blue-600'
              : 'text-gray-600 hover:text-gray-800'
          }`}
          onClick={() => setActiveTab('distributions')}
        >
          Distributions ({data.distributions.count})
        </button>
        <button
          className={`px-4 py-2 text-sm font-medium rounded-t-lg ${
            activeTab === 'errors'
              ? 'bg-white border-b-2 border-blue-500 text-blue-600'
              : 'text-gray-600 hover:text-gray-800'
          }`}
          onClick={() => setActiveTab('errors')}
        >
          Validation Issues ({data.validation_errors.data.length})
        </button>
      </div>

      {/* Content based on active tab */}
      {activeTab === 'distributions' && (
        <Card>
          <CardHeader>
            <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
              <CardTitle>Distribution Data</CardTitle>

              {/* Search and Filter Controls */}
              <div className="flex flex-col sm:flex-row gap-2 w-full sm:w-auto">
                <Input
                  placeholder="Search investors..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full sm:w-64"
                />
                <select
                  value={filterJurisdiction}
                  onChange={(e) => setFilterJurisdiction(e.target.value)}
                  className="px-3 py-2 border rounded-md bg-white"
                >
                  <option value="all">All Jurisdictions</option>
                  {jurisdictions.map(jurisdiction => (
                    <option key={jurisdiction} value={jurisdiction}>
                      {jurisdiction}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {showPreviewOnly && (
              <p className="text-sm text-gray-600">
                Showing first {Math.min(previewLimit, data.distributions.count)} of {data.distributions.count} distributions
              </p>
            )}
          </CardHeader>

          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Investor Name</TableHead>
                    <TableHead>Entity Type</TableHead>
                    <TableHead>Tax State</TableHead>
                    <TableHead>Fund Code</TableHead>
                    <TableHead>Period</TableHead>
                    <TableHead>Jurisdiction</TableHead>
                    <TableHead className="text-right">Amount</TableHead>
                    <TableHead>Composite</TableHead>
                    <TableHead>Withholding</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredDistributions.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={9} className="text-center py-8 text-gray-500">
                        {searchTerm || filterJurisdiction !== 'all'
                          ? 'No distributions match your filters'
                          : 'No distribution data available'
                        }
                      </TableCell>
                    </TableRow>
                  ) : (
                    filteredDistributions.map((distribution) => (
                      <TableRow key={distribution.id}>
                        <TableCell className="font-medium">
                          {distribution.investor_name}
                        </TableCell>
                        <TableCell>{distribution.entity_type}</TableCell>
                        <TableCell>{distribution.tax_state}</TableCell>
                        <TableCell>{distribution.fund_code}</TableCell>
                        <TableCell>{distribution.period}</TableCell>
                        <TableCell>
                          <Badge variant="secondary">{distribution.jurisdiction}</Badge>
                        </TableCell>
                        <TableCell className="text-right font-mono">
                          {formatCurrency(distribution.amount)}
                        </TableCell>
                        <TableCell>
                          <Badge
                            variant={distribution.composite_exemption ? "default" : "secondary"}
                            className={distribution.composite_exemption ? "bg-green-100 text-green-800" : ""}
                          >
                            {distribution.composite_exemption ? 'Exempt' : 'Taxable'}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <Badge
                            variant={distribution.withholding_exemption ? "default" : "secondary"}
                            className={distribution.withholding_exemption ? "bg-green-100 text-green-800" : ""}
                          >
                            {distribution.withholding_exemption ? 'Exempt' : 'Taxable'}
                          </Badge>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      )}

      {activeTab === 'errors' && (
        <Card>
          <CardHeader>
            <CardTitle>Validation Errors & Warnings</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Row</TableHead>
                    <TableHead>Column</TableHead>
                    <TableHead>Severity</TableHead>
                    <TableHead>Error Code</TableHead>
                    <TableHead>Message</TableHead>
                    <TableHead>Value</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {data.validation_errors.data.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={6} className="text-center py-8 text-gray-500">
                        No validation errors found
                      </TableCell>
                    </TableRow>
                  ) : (
                    data.validation_errors.data.map((error, index) => (
                      <TableRow key={index}>
                        <TableCell>{error.row_number}</TableCell>
                        <TableCell>{error.column_name}</TableCell>
                        <TableCell>
                          <Badge
                            variant={error.severity === 'ERROR' ? "destructive" : "default"}
                            className={error.severity === 'WARNING' ? "bg-yellow-100 text-yellow-800" : ""}
                          >
                            {error.severity}
                          </Badge>
                        </TableCell>
                        <TableCell className="font-mono text-sm">
                          {error.error_code}
                        </TableCell>
                        <TableCell>{error.error_message}</TableCell>
                        <TableCell className="font-mono text-sm text-gray-600">
                          {error.field_value || '-'}
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};