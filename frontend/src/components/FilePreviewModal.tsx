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
  jurisdiction: string;
  amount: number;
  composite_exemption: string;
  withholding_exemption: string;
  fund_code: string;
  period: string;
}

interface GroupedInvestorData {
  investor_name: string;
  entity_type: string;
  tax_state: string;
  fund_code: string;
  period: string;
  distributions: Record<string, number>;
  composite_exemptions: Record<string, string>;
  withholding_exemptions: Record<string, string>;
}

interface PreviewResponse {
  session_id: string;
  status: string;
  preview_data: PreviewData[];
  total_records: number;
  preview_limit: number;
  showing_count: number;
}

export default function FilePreviewModal({ isOpen, onClose, sessionId, filename }: FilePreviewModalProps) {
  const [previewData, setPreviewData] = useState<PreviewResponse | null>(null);
  const [groupedData, setGroupedData] = useState<GroupedInvestorData[]>([]);
  const [jurisdictions, setJurisdictions] = useState<string[]>([]);
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
      const data = await api.getResultsPreview(sessionId, 50); // Show first 50 rows
      setPreviewData(data);

      // Transform data for grouped display
      if (data.preview_data && data.preview_data.length > 0) {
        const { grouped, jurisdictions } = transformDataByInvestor(data.preview_data);
        setGroupedData(grouped);
        setJurisdictions(jurisdictions);
      }
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

  const transformDataByInvestor = (data: PreviewData[]): { grouped: GroupedInvestorData[], jurisdictions: string[] } => {
    const investorMap = new Map<string, GroupedInvestorData>();
    const jurisdictionSet = new Set<string>();

    data.forEach(row => {
      const key = row.investor_name;
      jurisdictionSet.add(row.jurisdiction);

      if (!investorMap.has(key)) {
        investorMap.set(key, {
          investor_name: row.investor_name,
          entity_type: row.entity_type,
          tax_state: row.tax_state,
          fund_code: row.fund_code,
          period: row.period,
          distributions: {},
          composite_exemptions: {},
          withholding_exemptions: {}
        });
      }

      const investor = investorMap.get(key)!;
      investor.distributions[row.jurisdiction] = row.amount;
      investor.composite_exemptions[row.jurisdiction] = row.composite_exemption;
      investor.withholding_exemptions[row.jurisdiction] = row.withholding_exemption;
    });

    const sortedJurisdictions = Array.from(jurisdictionSet).sort();
    return {
      grouped: Array.from(investorMap.values()),
      jurisdictions: sortedJurisdictions
    };
  };


  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-7xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">Results Preview</h2>
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
                <h3 className="font-medium text-blue-900 mb-2">Results Preview</h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div>
                    <span className="text-blue-600 font-medium">Status:</span>
                    <span className="ml-2 text-blue-900 capitalize">{previewData.status}</span>
                  </div>
                  <div>
                    <span className="text-blue-600 font-medium">Total Records:</span>
                    <span className="ml-2 text-blue-900">{previewData.total_records.toLocaleString()}</span>
                  </div>
                  <div>
                    <span className="text-blue-600 font-medium">Showing:</span>
                    <span className="ml-2 text-blue-900">{groupedData.length} investors ({previewData.showing_count} distributions)</span>
                  </div>
                  <div>
                    <span className="text-blue-600 font-medium">Fund:</span>
                    <span className="ml-2 text-blue-900">{previewData.preview_data[0]?.fund_code || 'N/A'}</span>
                  </div>
                </div>
              </div>

              {/* Data Table */}
              <div className="border border-gray-200 rounded-lg overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        {/* Fixed investor columns */}
                        <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider sticky left-0 bg-gray-50 z-10">
                          Investor Name
                        </th>
                        <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Entity Type
                        </th>
                        <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Tax State
                        </th>

                        {/* Dynamic distribution columns */}
                        {jurisdictions.map(jurisdiction => (
                          <th key={`dist-${jurisdiction}`} className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Distribution {jurisdiction}
                          </th>
                        ))}

                        {/* Dynamic exemption columns */}
                        {jurisdictions.map(jurisdiction => (
                          <th key={`comp-${jurisdiction}`} className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Composite {jurisdiction}
                          </th>
                        ))}
                        {jurisdictions.map(jurisdiction => (
                          <th key={`with-${jurisdiction}`} className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Withholding {jurisdiction}
                          </th>
                        ))}

                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Period
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {groupedData.map((investor, index) => (
                        <tr key={index} className="hover:bg-gray-50">
                          {/* Fixed investor columns */}
                          <td className="px-4 py-3 text-sm font-medium text-gray-900 text-center sticky left-0 bg-white hover:bg-gray-50 z-10">
                            {investor.investor_name}
                          </td>
                          <td className="px-4 py-3 text-sm text-gray-500 text-center">
                            {investor.entity_type}
                          </td>
                          <td className="px-4 py-3 text-sm text-gray-500 text-center">
                            {investor.tax_state}
                          </td>

                          {/* Dynamic distribution amounts */}
                          {jurisdictions.map(jurisdiction => (
                            <td key={`dist-${jurisdiction}`} className="px-4 py-3 text-sm text-gray-900 text-center font-medium">
                              {investor.distributions[jurisdiction] ? formatAmount(investor.distributions[jurisdiction]) : '-'}
                            </td>
                          ))}

                          {/* Dynamic composite exemptions */}
                          {jurisdictions.map(jurisdiction => (
                            <td key={`comp-${jurisdiction}`} className="px-4 py-3 text-center">
                              {investor.composite_exemptions[jurisdiction] ? (
                                <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
                                  investor.composite_exemptions[jurisdiction] === 'Yes'
                                    ? 'bg-green-100 text-green-800'
                                    : 'bg-gray-100 text-gray-800'
                                }`}>
                                  {investor.composite_exemptions[jurisdiction]}
                                </span>
                              ) : (
                                <span className="text-gray-400">-</span>
                              )}
                            </td>
                          ))}

                          {/* Dynamic withholding exemptions */}
                          {jurisdictions.map(jurisdiction => (
                            <td key={`with-${jurisdiction}`} className="px-4 py-3 text-center">
                              {investor.withholding_exemptions[jurisdiction] ? (
                                <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
                                  investor.withholding_exemptions[jurisdiction] === 'Yes'
                                    ? 'bg-green-100 text-green-800'
                                    : 'bg-gray-100 text-gray-800'
                                }`}>
                                  {investor.withholding_exemptions[jurisdiction]}
                                </span>
                              ) : (
                                <span className="text-gray-400">-</span>
                              )}
                            </td>
                          ))}

                          <td className="px-4 py-3 text-sm text-gray-500">
                            {investor.period}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {previewData.total_records > previewData.showing_count && (
                <div className="text-center p-4 bg-gray-50 rounded-lg">
                  <p className="text-sm text-gray-600">
                    Showing {groupedData.length} investors with {previewData.showing_count} of {previewData.total_records.toLocaleString()} distribution records.
                    <span className="ml-1">Data is grouped by investor with distributions across jurisdictions.</span>
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