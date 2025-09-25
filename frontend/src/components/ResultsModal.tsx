import React, { useEffect, useState } from 'react';
import { XMarkIcon, ArrowDownTrayIcon } from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';
import { api } from '../api/client';
import type { ResultsPreviewResponse, ResultsPreviewRow } from '../types/api';

type ResultsModalProps = {
  isOpen: boolean;
  onClose: () => void;
  sessionId: string | null;
  filename?: string;
};

type GroupedResults = {
  investor_name: string;
  entity_type: string;
  tax_state: string;
  fund_code: string;
  period: string;
  distributions: Record<string, number>;
  withholdingTaxes: Record<string, number | null>;
  compositeTaxes: Record<string, number | null>;
};

const formatCurrency = (value: number | null | undefined) => {
  if (value === null || value === undefined) {
    return '-';
  }

  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
  }).format(value);
};

const groupResultsByInvestor = (
  rows: ResultsPreviewRow[],
): { grouped: GroupedResults[]; jurisdictions: string[] } => {
  const investorMap = new Map<string, GroupedResults>();
  const jurisdictions = new Set<string>();

  rows.forEach((row) => {
    const key = row.investor_name;
    jurisdictions.add(row.jurisdiction);

    if (!investorMap.has(key)) {
      investorMap.set(key, {
        investor_name: row.investor_name,
        entity_type: row.entity_type,
        tax_state: row.tax_state,
        fund_code: row.fund_code,
        period: row.period,
        distributions: {},
        withholdingTaxes: {},
        compositeTaxes: {},
      });
    }

    const investor = investorMap.get(key)!;
    investor.distributions[row.jurisdiction] = row.amount;
    investor.withholdingTaxes[row.jurisdiction] = row.withholding_tax_amount ?? null;
    investor.compositeTaxes[row.jurisdiction] = row.composite_tax_amount ?? null;
  });

  return {
    grouped: Array.from(investorMap.values()),
    jurisdictions: Array.from(jurisdictions).sort(),
  };
};

export default function ResultsModal({ isOpen, onClose, sessionId, filename }: ResultsModalProps) {
  const [preview, setPreview] = useState<ResultsPreviewResponse | null>(null);
  const [groupedResults, setGroupedResults] = useState<GroupedResults[]>([]);
  const [jurisdictions, setJurisdictions] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadPreviewData = async (currentSessionId: string) => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getResultsPreview(currentSessionId, 50, 'results');
      setPreview(data);

      if (data.preview_data.length > 0) {
        const { grouped, jurisdictions } = groupResultsByInvestor(data.preview_data);
        setGroupedResults(grouped);
        setJurisdictions(jurisdictions);
      } else {
        setGroupedResults([]);
        setJurisdictions([]);
      }
    } catch (err) {
      console.error('Failed to load calculation results preview', err);
      setError('Unable to load calculation results preview');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!isOpen || !sessionId) {
      return;
    }

    loadPreviewData(sessionId);
  }, [isOpen, sessionId]);

  if (!isOpen || !sessionId) {
    return null;
  }

  const handleDownloadReport = async () => {
    try {
      toast.loading('Preparing report...', { id: 'tax-report' });
      const blob = await api.downloadTaxReport(sessionId);
      const url = window.URL.createObjectURL(blob);
      const anchor = document.createElement('a');
      anchor.href = url;
      anchor.download = `tax_calculation_report_${sessionId}.csv`;
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      window.URL.revokeObjectURL(url);
      toast.success('Report downloaded successfully', { id: 'tax-report' });
    } catch (err) {
      console.error('Failed to download tax report', err);
      toast.error('Failed to download tax report', { id: 'tax-report' });
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-7xl w-full max-h-[90vh] overflow-hidden">
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">SALT Calculation Results</h2>
            {filename && <p className="text-sm text-gray-500 mt-1">{filename}</p>}
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
            aria-label="Close results"
          >
            <XMarkIcon className="h-6 w-6" />
          </button>
        </div>

        <div className="p-6 overflow-auto max-h-[calc(90vh-150px)]">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
              <span className="ml-3 text-gray-500">Loading results...</span>
            </div>
          ) : error ? (
            <div className="text-center py-12">
              <p className="text-red-600">{error}</p>
              <button onClick={() => loadPreviewData(sessionId)} className="mt-4 btn-primary">
                Retry
              </button>
            </div>
          ) : preview ? (
            <div className="space-y-4">
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h3 className="font-medium text-blue-900 mb-2">Session Summary</h3>
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4 text-sm">
                  <div>
                    <span className="text-blue-600 font-medium">Status:</span>
                    <span className="ml-2 text-blue-900 capitalize">{preview.status}</span>
                  </div>
                  <div>
                    <span className="text-blue-600 font-medium">Total Records:</span>
                    <span className="ml-2 text-blue-900">{preview.total_records.toLocaleString()}</span>
                  </div>
                  <div>
                    <span className="text-blue-600 font-medium">Showing:</span>
                    <span className="ml-2 text-blue-900">{preview.showing_count.toLocaleString()} distributions</span>
                  </div>
                  <div>
                    <span className="text-blue-600 font-medium">Fund:</span>
                    <span className="ml-2 text-blue-900">{preview.preview_data[0]?.fund_code || 'N/A'}</span>
                  </div>
                </div>
              </div>

              <div className="border border-gray-200 rounded-lg overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider sticky left-0 bg-gray-50 z-10">
                          Investor Name
                        </th>
                        <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Entity Type
                        </th>
                        <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Tax State
                        </th>
                        {jurisdictions.map((jurisdiction) => (
                          <th key={`dist-${jurisdiction}`} className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Distribution {jurisdiction}
                          </th>
                        ))}
                        {jurisdictions.map((jurisdiction) => (
                          <th key={`with-${jurisdiction}`} className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Withholding Tax {jurisdiction}
                          </th>
                        ))}
                        {jurisdictions.map((jurisdiction) => (
                          <th key={`comp-${jurisdiction}`} className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Composite Tax {jurisdiction}
                          </th>
                        ))}
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                          Period
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {groupedResults.map((investor, index) => (
                        <tr key={`${investor.investor_name}-${index}`} className="hover:bg-gray-50">
                          <td className="px-4 py-3 text-sm font-medium text-gray-900 text-center sticky left-0 bg-white z-10">
                            {investor.investor_name}
                          </td>
                          <td className="px-4 py-3 text-sm text-gray-500 text-center">
                            {investor.entity_type}
                          </td>
                          <td className="px-4 py-3 text-sm text-gray-500 text-center">
                            {investor.tax_state}
                          </td>
                          {jurisdictions.map((jurisdiction) => (
                            <td key={`dist-${jurisdiction}`} className="px-4 py-3 text-sm text-gray-900 text-center font-medium">
                              {formatCurrency(investor.distributions[jurisdiction] ?? null)}
                            </td>
                          ))}
                          {jurisdictions.map((jurisdiction) => (
                            <td key={`with-${jurisdiction}`} className="px-4 py-3 text-sm text-gray-900 text-center">
                              {formatCurrency(investor.withholdingTaxes[jurisdiction])}
                            </td>
                          ))}
                          {jurisdictions.map((jurisdiction) => (
                            <td key={`comp-${jurisdiction}`} className="px-4 py-3 text-sm text-gray-900 text-center">
                              {formatCurrency(investor.compositeTaxes[jurisdiction])}
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
            </div>
          ) : null}
        </div>

        <div className="flex justify-end gap-3 p-6 border-t border-gray-200">
          <button
            onClick={handleDownloadReport}
            className="btn-primary inline-flex items-center"
          >
            <ArrowDownTrayIcon className="h-4 w-4 mr-2" />
            Download Report
          </button>
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
