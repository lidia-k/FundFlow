import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  ArrowLeft,
  Rocket,
  Eye,
  FileText,
  Filter,
  Download,
  CheckCircle2,
  XCircle
} from 'lucide-react';
import { saltRulesApi } from '../api/saltRules';
import type { RuleSet, RulePreview as RulePreviewType } from '../types/saltRules';
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
  Input,
  useToast,
} from '@/components/ui';

export default function RulePreview() {
  const { ruleSetId } = useParams<{ ruleSetId: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();

  const [ruleSet, setRuleSet] = useState<RuleSet | null>(null);
  const [preview, setPreview] = useState<RulePreviewType | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [publishing, setPublishing] = useState(false);
  const [stateFilter, setStateFilter] = useState('');
  const [showConfirmPublish, setShowConfirmPublish] = useState(false);

  useEffect(() => {
    if (ruleSetId) {
      loadPreviewData();
    }
  }, [ruleSetId]);

  const loadPreviewData = async () => {
    if (!ruleSetId) return;

    try {
      setLoading(true);
      setError(null);

      const [ruleSetData, previewData] = await Promise.all([
        saltRulesApi.getDetails(ruleSetId),
        saltRulesApi.getPreview(ruleSetId)
      ]);

      setRuleSet(ruleSetData);
      setPreview(previewData);
    } catch (error: any) {
      console.error('Failed to load preview data:', error);
      setError('Failed to load rule preview. Please try again.');
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

      // Navigate back to rule set details
      navigate(`/salt-rules/${ruleSetId}`);

    } catch (error: any) {
      console.error('Failed to publish rules:', error);
      toast({
        title: "Publish failed",
        description: error.response?.data?.message || "Please try again later",
        variant: "destructive",
      });
    } finally {
      setPublishing(false);
      setShowConfirmPublish(false);
    }
  };

  const filteredRules = preview?.preview.addedRules.filter(rule =>
    stateFilter === '' || rule.state.toLowerCase().includes(stateFilter.toLowerCase())
  ) || [];

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto space-y-8 p-6">
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          <p className="mt-4 text-gray-500">Loading rule preview...</p>
        </div>
      </div>
    );
  }

  if (error || !ruleSet || !preview) {
    return (
      <div className="max-w-7xl mx-auto space-y-8 p-6">
        <Alert variant="destructive">
          <XCircle className="h-4 w-4" />
          <AlertDescription>
            {error || 'Preview data not found'}
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto space-y-8 p-6">
      {/* Header with Navigation */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Link
            to={`/salt-rules/${ruleSetId}`}
            className="inline-flex items-center text-sm text-gray-600 hover:text-gray-900"
          >
            <ArrowLeft className="h-4 w-4 mr-1" />
            Back to Rule Set Details
          </Link>
        </div>

        {ruleSet.status === 'validated' && (
          <Button
            onClick={() => setShowConfirmPublish(true)}
            disabled={publishing}
            size="lg"
          >
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

      {/* Preview Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Eye className="h-5 w-5" />
                Rule Preview: {ruleSet.filename}
              </CardTitle>
              <CardDescription>
                Review the SALT rules before publishing to the live system
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">{preview.changes.added}</div>
              <div className="text-sm text-gray-500">Rules to Add</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">{preview.changes.modified}</div>
              <div className="text-sm text-gray-500">Rules to Modify</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-red-600">{preview.changes.removed}</div>
              <div className="text-sm text-gray-500">Rules to Remove</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Rules Table */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5" />
              SALT Rules ({filteredRules.length} rules)
            </CardTitle>
            <div className="flex items-center space-x-2">
              <Filter className="h-4 w-4 text-gray-400" />
              <Input
                placeholder="Filter by state..."
                value={stateFilter}
                onChange={(e) => setStateFilter(e.target.value)}
                className="w-48"
              />
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {filteredRules.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-gray-500">No rules found matching your filter.</p>
            </div>
          ) : (
            <div className="overflow-hidden">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      State
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Entity
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Tax Type
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Rate
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Effective Date
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Description
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {filteredRules.slice(0, 100).map((rule, index) => (
                    <tr key={rule.id || index} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="font-medium text-gray-900">{rule.state}</span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {rule.entity}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <Badge variant="outline">{rule.taxType}</Badge>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {(rule.rate * 100).toFixed(2)}%
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {rule.effectiveDate || 'N/A'}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-500 max-w-xs truncate">
                        {rule.description || 'No description'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>

              {filteredRules.length > 100 && (
                <div className="px-6 py-4 bg-gray-50 text-center">
                  <p className="text-sm text-gray-500">
                    Showing first 100 rules. {filteredRules.length - 100} more rules available.
                  </p>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Publish Confirmation Modal */}
      {showConfirmPublish && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <Card className="w-full max-w-md">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Rocket className="h-5 w-5" />
                Confirm Publish
              </CardTitle>
              <CardDescription>
                Are you sure you want to publish these SALT rules?
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <Alert>
                <CheckCircle2 className="h-4 w-4" />
                <AlertDescription>
                  This will make {preview.changes.added + preview.changes.modified} rules active in the SALT calculation system.
                </AlertDescription>
              </Alert>

              <div className="flex items-center justify-end space-x-3">
                <Button
                  variant="outline"
                  onClick={() => setShowConfirmPublish(false)}
                  disabled={publishing}
                >
                  Cancel
                </Button>
                <Button
                  onClick={handlePublish}
                  disabled={publishing}
                >
                  {publishing ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-current mr-2" />
                      Publishing...
                    </>
                  ) : (
                    'Confirm Publish'
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Status Messages */}
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