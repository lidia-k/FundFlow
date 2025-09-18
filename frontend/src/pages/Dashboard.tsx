import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { CloudArrowUpIcon, DocumentTextIcon, ChartBarIcon, TrashIcon } from '@heroicons/react/24/outline';
import { api } from '../api/client';
import type { SessionInfo } from '../types/api';
import FilePreviewModal from '../components/FilePreviewModal';
import DeleteConfirmationModal from '../components/DeleteConfirmationModal';

export default function Dashboard() {
  const [sessions, setSessions] = useState<SessionInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [previewModal, setPreviewModal] = useState<{
    isOpen: boolean;
    sessionId: string;
    filename: string;
  }>({
    isOpen: false,
    sessionId: '',
    filename: '',
  });

  const [deleteModal, setDeleteModal] = useState<{
    isOpen: boolean;
    sessionId: string;
    filename: string;
  }>({
    isOpen: false,
    sessionId: '',
    filename: '',
  });

  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => {
    loadSessions();
  }, []);

  const loadSessions = async () => {
    try {
      const data = await api.getSessions();
      setSessions(data);
    } catch (error) {
      console.error('Failed to load sessions:', error);
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
      case 'completed':
        return 'text-green-600 bg-green-100';
      case 'failed':
        return 'text-red-600 bg-red-100';
      case 'processing':
        return 'text-yellow-600 bg-yellow-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  const handleFileNameClick = (session: SessionInfo) => {
    setPreviewModal({
      isOpen: true,
      sessionId: session.session_id,
      filename: session.filename,
    });
  };

  const handleClosePreview = () => {
    setPreviewModal({
      isOpen: false,
      sessionId: '',
      filename: '',
    });
  };

  const handleDeleteClick = (session: SessionInfo) => {
    setDeleteModal({
      isOpen: true,
      sessionId: session.session_id,
      filename: session.filename,
    });
  };

  const handleCloseDelete = () => {
    setDeleteModal({
      isOpen: false,
      sessionId: '',
      filename: '',
    });
  };

  const handleConfirmDelete = async () => {
    if (!deleteModal.sessionId) return;

    setIsDeleting(true);
    try {
      await api.deleteSession(deleteModal.sessionId);

      // Remove the session from the local state
      setSessions(prevSessions =>
        prevSessions.filter(session => session.session_id !== deleteModal.sessionId)
      );

      // Close the modal
      handleCloseDelete();

      // Show success message (you could add a toast notification here)
      console.log('Session deleted successfully');
    } catch (error) {
      console.error('Failed to delete session:', error);
      // Show error message (you could add a toast notification here)
      alert('Failed to delete the calculation. Please try again.');
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <p className="mt-2 text-gray-600">
          Welcome to FundFlow SALT calculation platform
        </p>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
        <Link
          to="/upload"
          className="card p-6 hover:shadow-md transition-shadow cursor-pointer"
        >
          <div className="flex items-center">
            <CloudArrowUpIcon className="h-8 w-8 text-primary-600" />
            <div className="ml-4">
              <h3 className="text-lg font-medium text-gray-900">Upload File</h3>
              <p className="text-sm text-gray-500">Start a new SALT calculation</p>
            </div>
          </div>
        </Link>

        <a
          href="/api/template"
          download
          className="card p-6 hover:shadow-md transition-shadow cursor-pointer"
        >
          <div className="flex items-center">
            <DocumentTextIcon className="h-8 w-8 text-primary-600" />
            <div className="ml-4">
              <h3 className="text-lg font-medium text-gray-900">Download Template</h3>
              <p className="text-sm text-gray-500">Get the Excel template</p>
            </div>
          </div>
        </a>

        <div className="card p-6">
          <div className="flex items-center">
            <ChartBarIcon className="h-8 w-8 text-primary-600" />
            <div className="ml-4">
              <h3 className="text-lg font-medium text-gray-900">Recent Calculations</h3>
              <p className="text-sm text-gray-500">{sessions.length} calculations</p>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Calculations */}
      <div className="card">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-medium text-gray-900">Recent Calculations</h2>
        </div>
        
        {loading ? (
          <div className="p-6 text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto"></div>
            <p className="mt-2 text-gray-500">Loading...</p>
          </div>
        ) : sessions.length === 0 ? (
          <div className="p-6 text-center">
            <CloudArrowUpIcon className="h-12 w-12 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-500">No calculations yet</p>
            <Link to="/upload" className="btn-primary mt-4">
              Start Your First Calculation
            </Link>
          </div>
        ) : (
          <div className="overflow-hidden">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    File
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
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
                {sessions.slice(0, 10).map((session) => (
                  <tr key={session.session_id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-primary-600 hover:text-primary-900 cursor-pointer" onClick={() => handleFileNameClick(session)}>
                        {session.filename}
                      </div>
                      <div className="text-sm text-gray-500">
                        ID: {session.session_id.slice(0, 8)}...
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(session.status)}`}>
                        {session.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {formatDate(session.created_at)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <div className="flex items-center space-x-4">
                        <Link
                          to={`/results/${session.session_id}`}
                          className="text-primary-600 hover:text-primary-900"
                        >
                          View Results
                        </Link>
                        <button
                          onClick={() => handleDeleteClick(session)}
                          className="text-red-600 hover:text-red-900 p-1 rounded hover:bg-red-50 transition-colors"
                          title="Delete calculation"
                        >
                          <TrashIcon className="h-4 w-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* File Preview Modal */}
      <FilePreviewModal
        isOpen={previewModal.isOpen}
        onClose={handleClosePreview}
        sessionId={previewModal.sessionId}
        filename={previewModal.filename}
      />

      {/* Delete Confirmation Modal */}
      <DeleteConfirmationModal
        isOpen={deleteModal.isOpen}
        onClose={handleCloseDelete}
        onConfirm={handleConfirmDelete}
        sessionId={deleteModal.sessionId}
        filename={deleteModal.filename}
        isDeleting={isDeleting}
      />
    </div>
  );
}