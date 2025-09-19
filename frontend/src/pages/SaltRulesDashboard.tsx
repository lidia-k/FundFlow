import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { CloudArrowUpIcon, DocumentTextIcon, ChartBarIcon, TrashIcon } from '@heroicons/react/24/outline';
import { saltRulesApi } from '../api/saltRules';
import type { RuleSet } from '../types/saltRules';
import { ExclamationTriangleIcon, XMarkIcon } from '@heroicons/react/24/outline';
import SaltSetDetails from './SaltSetDetails';

export default function SaltRulesDashboard() {
  const [ruleSets, setRuleSets] = useState<RuleSet[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deleteModal, setDeleteModal] = useState<{
    isOpen: boolean;
    ruleSetId: string;
    ruleSetName: string;
  }>({
    isOpen: false,
    ruleSetId: '',
    ruleSetName: '',
  });
  const [isDeleting, setIsDeleting] = useState(false);
  const [detailsModal, setDetailsModal] = useState<{
    isOpen: boolean;
    ruleSetId: string;
  }>({
    isOpen: false,
    ruleSetId: '',
  });

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

  const handleDeleteClick = (ruleSet: RuleSet) => {
    setDeleteModal({
      isOpen: true,
      ruleSetId: ruleSet.id,
      ruleSetName: `${ruleSet.year} ${ruleSet.quarter} v${ruleSet.version}`,
    });
  };

  const handleCloseDelete = () => {
    setDeleteModal({
      isOpen: false,
      ruleSetId: '',
      ruleSetName: '',
    });
  };

  const handleConfirmDelete = async () => {
    if (!deleteModal.ruleSetId) return;

    setIsDeleting(true);
    try {
      await saltRulesApi.delete(deleteModal.ruleSetId);

      // Remove the rule set from the local state
      setRuleSets(prevRuleSets =>
        prevRuleSets.filter(ruleSet => ruleSet.id !== deleteModal.ruleSetId)
      );

      // Close the modal
      handleCloseDelete();

      // Show success message (you could add a toast notification here)
      console.log('Rule set deleted successfully');
    } catch (error) {
      console.error('Failed to delete rule set:', error);
      // Show error message (you could add a toast notification here)
      alert('Failed to delete the rule set. Please try again.');
    } finally {
      setIsDeleting(false);
    }
  };

  const handleViewDetails = (ruleSet: RuleSet) => {
    setDetailsModal({
      isOpen: true,
      ruleSetId: ruleSet.id,
    });
  };

  const handleCloseDetails = () => {
    setDetailsModal({
      isOpen: false,
      ruleSetId: '',
    });
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
                      <div className="flex items-center space-x-4">
                        <button
                          onClick={() => handleViewDetails(ruleSet)}
                          className="text-primary-600 hover:text-primary-900"
                        >
                          View Details
                        </button>
                        {ruleSet.status !== 'active' && (
                          <button
                            onClick={() => handleDeleteClick(ruleSet)}
                            className="text-red-600 hover:text-red-900 p-1 rounded hover:bg-red-50 transition-colors"
                            title="Delete rule set"
                          >
                            <TrashIcon className="h-4 w-4" />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Delete Confirmation Modal */}
      {deleteModal.isOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-md w-full">
            {/* Header */}
            <div className="flex items-center justify-between p-6 border-b border-gray-200">
              <div className="flex items-center">
                <ExclamationTriangleIcon className="h-6 w-6 text-red-600 mr-3" />
                <h2 className="text-lg font-semibold text-gray-900">Delete Rule Set</h2>
              </div>
              <button
                onClick={handleCloseDelete}
                disabled={isDeleting}
                className="text-gray-400 hover:text-gray-600 transition-colors disabled:opacity-50"
              >
                <XMarkIcon className="h-6 w-6" />
              </button>
            </div>

            {/* Content */}
            <div className="p-6">
              <div className="space-y-4">
                <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                  <div className="flex">
                    <ExclamationTriangleIcon className="h-5 w-5 text-red-400 flex-shrink-0 mt-0.5" />
                    <div className="ml-3">
                      <h3 className="text-sm font-medium text-red-800">
                        This action cannot be undone
                      </h3>
                      <p className="mt-1 text-sm text-red-700">
                        This will permanently delete the rule set and all associated SALT rules.
                      </p>
                    </div>
                  </div>
                </div>

                <div>
                  <p className="text-sm text-gray-600 mb-3">
                    Are you sure you want to delete this rule set?
                  </p>

                  <div className="bg-gray-50 rounded-lg p-3 space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="font-medium text-gray-600">Rule Set:</span>
                      <span className="text-gray-900">{deleteModal.ruleSetName}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="font-medium text-gray-600">ID:</span>
                      <span className="text-gray-900 font-mono">{deleteModal.ruleSetId.slice(0, 8)}...</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Footer */}
            <div className="flex justify-end gap-3 p-6 border-t border-gray-200">
              <button
                onClick={handleCloseDelete}
                disabled={isDeleting}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Cancel
              </button>
              <button
                onClick={handleConfirmDelete}
                disabled={isDeleting}
                className="px-4 py-2 text-sm font-medium text-white bg-red-600 border border-transparent rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
              >
                {isDeleting ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Deleting...
                  </>
                ) : (
                  'Delete Rule Set'
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Rule Set Details Modal */}
      <SaltSetDetails
        isOpen={detailsModal.isOpen}
        onClose={handleCloseDetails}
        ruleSetId={detailsModal.ruleSetId}
      />
    </div>
  );
}