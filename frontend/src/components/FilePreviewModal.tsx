import React, { useState, useEffect } from 'react';
import { XMarkIcon } from '@heroicons/react/24/outline';
import { api } from '../api/client';

interface FilePreviewModalProps {
  isOpen: boolean;
  onClose: () => void;
  sessionId: string;
  filename: string;
}

interface PreviewData {
  investor_name: string;
  entity_type: string;
  tax_state: string;
  distributions: Record<string, number>;
  composite_exemptions: Record<string, string>;
  withholding_exemptions: Record<string, string>;
  fund_code: string;
  period: string;
}

interface PreviewResponse {
  session_id: string;
  filename: string;
  status: string;
  file_info: {
    fund_code: string;
    period_quarter: string;
    period_year: string;
    file_format: string;
  };
  preview_data: PreviewData[];
  available_states: {
    distributions: string[];
    exemptions: string[];
  };
  total_rows: number;
  valid_rows: number;
  preview_limit: number;
  showing_count: number;
  has_errors: boolean;
  error_count: number;
}

export default function FilePreviewModal({ isOpen, onClose, sessionId, filename }: FilePreviewModalProps) {
  const [previewData, setPreviewData] = useState<PreviewResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen && sessionId) {
      loadPreviewData();
    }
  }, [isOpen, sessionId]);

  const loadPreviewData = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getFilePreview(sessionId, 50); // Show first 50 rows
      setPreviewData(data);
    } catch (err) {
      console.error('Failed to load preview data:', err);
      setError('Failed to load file preview');
    } finally {
      setLoading(false);
    }
  };

  const formatAmount = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-7xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">File Preview</h2>
            <p className="text-sm text-gray-500 mt-1">{filename}</p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <XMarkIcon className="h-6 w-6" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-auto max-h-[calc(90vh-140px)]">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
              <span className="ml-3 text-gray-500">Loading preview...</span>
            </div>
          ) : error ? (
            <div className="text-center py-12">
              <p className="text-red-600">{error}</p>
              <button
                onClick={loadPreviewData}
                className="mt-4 btn-primary"
              >
                Retry
              </button>
            </div>
          ) : previewData ? (
            <div className="space-y-4">
              {/* Summary */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h3 className="font-medium text-blue-900 mb-2">File Summary</h3>
                <div className="grid grid-cols-2 md:grid-cols-5 gap-4 text-sm">
                  <div>
                    <span className="text-blue-600 font-medium">Status:</span>
                    <span className="ml-2 text-blue-900 capitalize">{previewData.status}</span>
                  </div>
                  <div>
                    <span className="text-blue-600 font-medium">Total Rows:</span>
                    <span className="ml-2 text-blue-900">{previewData.total_rows.toLocaleString()}</span>
                  </div>
                  <div>
                    <span className="text-blue-600 font-medium">Valid Rows:</span>
                    <span className="ml-2 text-blue-900">{previewData.valid_rows.toLocaleString()}</span>
                  </div>
                  <div>
                    <span className="text-blue-600 font-medium">Showing:</span>
                    <span className="ml-2 text-blue-900">{previewData.showing_count} of {previewData.total_rows}</span>
                  </div>
                  <div>
                    <span className="text-blue-600 font-medium">Fund:</span>
                    <span className="ml-2 text-blue-900">{previewData.file_info.fund_code || 'N/A'}</span>
                  </div>
                </div>
                {previewData.has_errors && (
                  <div className="mt-3 p-2 bg-yellow-50 border border-yellow-200 rounded">
                    <span className="text-yellow-800 text-sm font-medium">
                      ⚠️ {previewData.error_count} validation error{previewData.error_count !== 1 ? 's' : ''} found
                    </span>
                  </div>
                )}
              </div>

              {/* Data Table */}
              <div className="border border-gray-200 rounded-lg overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        {/* Fixed columns */}
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Investor Name
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Entity Type
                        </th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Tax State
                        </th>

                        {/* Dynamic distribution columns */}
                        {previewData.available_states.distributions.map((state) => (
                          <th key={`dist-${state}`} className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                            {state} Amount
                          </th>
                        ))}

                        {/* Dynamic exemption columns */}
                        {previewData.available_states.exemptions.map((state) => (
                          <React.Fragment key={`exempt-${state}`}>
                            <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                              {state} Composite
                            </th>
                            <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                              {state} Withholding
                            </th>
                          </React.Fragment>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {previewData.preview_data.map((row, index) => (
                        <tr key={index} className="hover:bg-gray-50">
                          {/* Fixed columns */}
                          <td className="px-4 py-3 text-sm font-medium text-gray-900">
                            {row.investor_name}
                          </td>
                          <td className="px-4 py-3 text-sm text-gray-500">
                            {row.entity_type}
                          </td>
                          <td className="px-4 py-3 text-sm text-gray-500">
                            {row.tax_state}
                          </td>

                          {/* Dynamic distribution amounts */}
                          {previewData.available_states.distributions.map((state) => (
                            <td key={`dist-${state}`} className="px-4 py-3 text-sm text-gray-900 text-right font-medium">
                              {formatAmount(row.distributions[state] || 0)}
                            </td>
                          ))}

                          {/* Dynamic exemptions */}
                          {previewData.available_states.exemptions.map((state) => (
                            <React.Fragment key={`exempt-${state}`}>
                              <td className="px-4 py-3 text-center">
                                <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
                                  row.composite_exemptions[state] === 'Yes'
                                    ? 'bg-green-100 text-green-800'
                                    : 'bg-gray-100 text-gray-800'
                                }`}>
                                  {row.composite_exemptions[state] || 'No'}
                                </span>
                              </td>
                              <td className="px-4 py-3 text-center">
                                <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
                                  row.withholding_exemptions[state] === 'Yes'
                                    ? 'bg-green-100 text-green-800'
                                    : 'bg-gray-100 text-gray-800'
                                }`}>
                                  {row.withholding_exemptions[state] || 'No'}
                                </span>
                              </td>
                            </React.Fragment>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {previewData.total_rows > previewData.showing_count && (
                <div className="text-center p-4 bg-gray-50 rounded-lg">
                  <p className="text-sm text-gray-600">
                    Showing first {previewData.showing_count} of {previewData.total_rows.toLocaleString()} rows from the uploaded file.
                    <span className="ml-1">This is the raw data before processing.</span>
                  </p>
                </div>
              )}
            </div>
          ) : null}
        </div>

        {/* Footer */}
        <div className="flex justify-end gap-3 p-6 border-t border-gray-200">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}