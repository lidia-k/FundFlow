import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { CloudArrowUpIcon, DocumentTextIcon, ChartBarIcon } from '@heroicons/react/24/outline';
import { saltRulesApi } from '../api/saltRules';
import type { RuleSet } from '../types/saltRules';

export default function SaltRulesDashboard() {
  const [ruleSets, setRuleSets] = useState<RuleSet[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadRuleSets();
  }, []);

  const loadRuleSets = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await saltRulesApi.list();
      setRuleSets(response.items);
    } catch (error) {
      console.error('Failed to load rule sets:', error);

      // Extract detailed error message from backend response
      let errorMessage = 'Failed to load rule sets. Please try again.';
      if (error instanceof Error) {
        errorMessage = error.message;
      } else if (typeof error === 'object' && error !== null) {
        const errorObj = error as any;
        if (errorObj.response?.data?.detail) {
          errorMessage = errorObj.response.data.detail;
        } else if (errorObj.response?.data?.message) {
          errorMessage = errorObj.response.data.message;
        } else if (errorObj.message) {
          errorMessage = errorObj.message;
        }
      }

      setError(errorMessage);
    } finally {
      setLoading(false);
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
      case 'active':
        return 'text-green-600 bg-green-100';
      case 'draft':
        return 'text-yellow-600 bg-yellow-100';
      case 'archived':
        return 'text-gray-600 bg-gray-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  const getStatusDisplay = (status: string) => {
    switch (status) {
      case 'draft':
        return 'Draft';
      case 'active':
        return 'Active';
      case 'archived':
        return 'Archived';
      default:
        return status;
    }
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">SALT Rules Management</h1>
          <p className="mt-2 text-gray-600">
            Manage SALT tax rules matrix upload, validation, and publishing
          </p>
        </div>
        <Link to="/salt-rules/upload" className="btn-primary">
          <CloudArrowUpIcon className="h-5 w-5 mr-2" />
          Upload Rules Matrix
        </Link>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
        <div className="card p-6">
          <div className="flex items-center">
            <DocumentTextIcon className="h-8 w-8 text-primary-600" />
            <div className="ml-4">
              <h3 className="text-lg font-medium text-gray-900">Total Rule Sets</h3>
              <p className="text-sm text-gray-500">{ruleSets.length} rule sets</p>
            </div>
          </div>
        </div>

        <div className="card p-6">
          <div className="flex items-center">
            <ChartBarIcon className="h-8 w-8 text-primary-600" />
            <div className="ml-4">
              <h3 className="text-lg font-medium text-gray-900">Published</h3>
              <p className="text-sm text-gray-500">
                {ruleSets.filter(rs => rs.status === 'active').length} active
              </p>
            </div>
          </div>
        </div>

        <div className="card p-6">
          <div className="flex items-center">
            <CloudArrowUpIcon className="h-8 w-8 text-primary-600" />
            <div className="ml-4">
              <h3 className="text-lg font-medium text-gray-900">Pending</h3>
              <p className="text-sm text-gray-500">
                {ruleSets.filter(rs => rs.status !== 'active').length} waiting
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Rule Sets Table */}
      <div className="card">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-medium text-gray-900">Rule Sets</h2>
        </div>

        {error && (
          <div className="p-6">
            <div className="bg-red-50 border border-red-200 rounded-md p-4">
              <p className="text-red-600">{error}</p>
              <button
                onClick={loadRuleSets}
                className="mt-2 text-sm text-red-600 hover:text-red-800 underline"
              >
                Try again
              </button>
            </div>
          </div>
        )}

        {loading ? (
          <div className="p-6 text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto"></div>
            <p className="mt-2 text-gray-500">Loading rule sets...</p>
          </div>
        ) : ruleSets.length === 0 && !error ? (
          <div className="p-6 text-center">
            <CloudArrowUpIcon className="h-12 w-12 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-500 mb-4">No rule sets uploaded yet</p>
            <Link to="/salt-rules/upload" className="btn-primary">
              Upload Your First Rule Set
            </Link>
          </div>
        ) : (
          <div className="overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Rule Set
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Rules Count
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Created
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {ruleSets.slice(0, 10).map((ruleSet) => (
                  <tr key={ruleSet.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">
                        {ruleSet.year} {ruleSet.quarter} v{ruleSet.version}
                      </div>
                      <div className="text-sm text-gray-500">
                        ID: {ruleSet.id.slice(0, 8)}...
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(ruleSet.status)}`}>
                        {getStatusDisplay(ruleSet.status)}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      <div>
                        {ruleSet.ruleCountWithholding} withholding
                      </div>
                      <div>
                        {ruleSet.ruleCountComposite} composite
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {formatDate(ruleSet.createdAt)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <Link
                        to={`/salt-rules/${ruleSet.id}`}
                        className="text-primary-600 hover:text-primary-900"
                      >
                        View Details
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}