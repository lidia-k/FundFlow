import React, { useState, useEffect } from 'react';
import { XMarkIcon } from '@heroicons/react/24/outline';
import { saltRulesApi } from '../api/saltRules';
import type { RuleSet, WithholdingRule, CompositeRule, StateWithholdingData, StateCompositeData } from '../types/saltRules';

interface SaltSetDetailsProps {
  isOpen: boolean;
  onClose: () => void;
  ruleSetId: string;
}

export default function SaltSetDetails({ isOpen, onClose, ruleSetId }: SaltSetDetailsProps) {
  const [ruleSet, setRuleSet] = useState<RuleSet | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'withholding' | 'composite'>('withholding');

  useEffect(() => {
    if (isOpen && ruleSetId) {
      loadRuleSetDetails();
    }
  }, [isOpen, ruleSetId]);

  const loadRuleSetDetails = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await saltRulesApi.getDetails(ruleSetId, true);
      setRuleSet(data);
    } catch (error) {
      console.error('Failed to load rule set details:', error);
      setError('Failed to load rule set details. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  // Data transformation functions
  const transformWithholdingRules = (rules: WithholdingRule[]): StateWithholdingData[] => {
    const stateGroups = rules.reduce((acc, rule) => {
      if (!acc[rule.stateCode]) {
        acc[rule.stateCode] = {
          state: rule.state,
          stateCode: rule.stateCode,
          individual: 0,
          estate: 0,
          trust: 0,
          partnership: 0,
          sCorporation: 0,
          corporation: 0,
          exemptOrg: 0,
          ira: 0,
          incomeThreshold: rule.incomeThreshold,
          taxThreshold: rule.taxThreshold,
        };
      }

      // Map entity types to the correct property
      const entityTypeMap: Record<string, keyof StateWithholdingData> = {
        'Individual': 'individual',
        'Estate': 'estate',
        'Trust': 'trust',
        'Partnership': 'partnership',
        'S Corporation': 'sCorporation',
        'Corporation': 'corporation',
        'Exempt Org': 'exemptOrg',
        'IRA': 'ira'
      };

      const entityKey = entityTypeMap[rule.entityType];
      if (entityKey && typeof acc[rule.stateCode][entityKey] === 'number') {
        (acc[rule.stateCode] as any)[entityKey] = rule.taxRate;
      }

      return acc;
    }, {} as Record<string, StateWithholdingData>);

    return Object.values(stateGroups).sort((a, b) => a.state.localeCompare(b.state));
  };

  const transformCompositeRules = (rules: CompositeRule[]): StateCompositeData[] => {
    const stateGroups = rules.reduce((acc, rule) => {
      if (!acc[rule.stateCode]) {
        acc[rule.stateCode] = {
          state: rule.state,
          stateCode: rule.stateCode,
          individual: 0,
          estate: 0,
          trust: 0,
          partnership: 0,
          sCorporation: 0,
          corporation: 0,
          exemptOrg: 0,
          ira: 0,
          incomeThreshold: rule.incomeThreshold,
          mandatory: rule.mandatoryFiling,
        };
      }

      // Map entity types to the correct property
      const entityTypeMap: Record<string, keyof StateCompositeData> = {
        'Individual': 'individual',
        'Estate': 'estate',
        'Trust': 'trust',
        'Partnership': 'partnership',
        'S Corporation': 'sCorporation',
        'Corporation': 'corporation',
        'Exempt Org': 'exemptOrg',
        'IRA': 'ira'
      };

      const entityKey = entityTypeMap[rule.entityType];
      if (entityKey && typeof acc[rule.stateCode][entityKey] === 'number') {
        (acc[rule.stateCode] as any)[entityKey] = rule.taxRate;
      }

      return acc;
    }, {} as Record<string, StateCompositeData>);

    return Object.values(stateGroups).sort((a, b) => a.state.localeCompare(b.state));
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-[95vw] w-full max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">
              SALT Rule Set Details
            </h2>
            {ruleSet && (
              <p className="text-sm text-gray-500 mt-1">
                {ruleSet.year} {ruleSet.quarter} v{ruleSet.version}
              </p>
            )}
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <XMarkIcon className="h-6 w-6" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-hidden">
          {loading ? (
            <div className="flex items-center justify-center h-64">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
              <p className="ml-3 text-gray-600">Loading rule details...</p>
            </div>
          ) : error ? (
            <div className="p-6">
              <div className="bg-red-50 border border-red-200 rounded-md p-4">
                <p className="text-red-600">{error}</p>
                <button
                  onClick={loadRuleSetDetails}
                  className="mt-2 text-sm text-red-600 hover:text-red-800 underline"
                >
                  Try again
                </button>
              </div>
            </div>
          ) : ruleSet ? (
            <>
              {/* Tab Navigation */}
              <div className="border-b border-gray-200">
                <nav className="flex space-x-8 px-6">
                  <button
                    onClick={() => setActiveTab('withholding')}
                    className={`py-4 px-1 border-b-2 font-medium text-sm ${
                      activeTab === 'withholding'
                        ? 'border-primary-500 text-primary-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }`}
                  >
                    Withholding Rules ({ruleSet.ruleCountWithholding})
                  </button>
                  <button
                    onClick={() => setActiveTab('composite')}
                    className={`py-4 px-1 border-b-2 font-medium text-sm ${
                      activeTab === 'composite'
                        ? 'border-primary-500 text-primary-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }`}
                  >
                    Composite Rules ({ruleSet.ruleCountComposite})
                  </button>
                </nav>
              </div>

              {/* Tab Content */}
              <div className="flex-1 overflow-hidden">
                {activeTab === 'withholding' ? (
                  <WithholdingRulesTable data={transformWithholdingRules(ruleSet.withholdingRules || [])} />
                ) : (
                  <CompositeRulesTable data={transformCompositeRules(ruleSet.compositeRules || [])} />
                )}
              </div>
            </>
          ) : null}
        </div>
      </div>
    </div>
  );
}

// Withholding Rules Table Component
function WithholdingRulesTable({ data }: { data: StateWithholdingData[] }) {
  if (data.length === 0) {
    return (
      <div className="p-6 text-center text-gray-500">
        No withholding rules found for this rule set.
      </div>
    );
  }

  return (
    <div className="overflow-x-auto overflow-y-auto max-h-[60vh] w-full">
      <table className="w-full divide-y divide-gray-200 border border-gray-200" style={{ minWidth: '1400px' }}>
        <thead className="bg-gray-50 sticky top-0">
          <tr>
            <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-r border-gray-200 min-w-[120px]">
              State
            </th>
            <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-r border-gray-200 min-w-[80px]">
              State Abbrev
            </th>
            <th className="px-3 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider border-r border-gray-200 min-w-[90px]">
              Individual
            </th>
            <th className="px-3 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider border-r border-gray-200 min-w-[80px]">
              Estate
            </th>
            <th className="px-3 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider border-r border-gray-200 min-w-[80px]">
              Trust
            </th>
            <th className="px-3 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider border-r border-gray-200 min-w-[100px]">
              Partnership
            </th>
            <th className="px-3 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider border-r border-gray-200 min-w-[110px]">
              S Corporation
            </th>
            <th className="px-3 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider border-r border-gray-200 min-w-[100px]">
              Corporation
            </th>
            <th className="px-3 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider border-r border-gray-200 min-w-[100px]">
              Exempt Org
            </th>
            <th className="px-3 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider border-r border-gray-200 min-w-[70px]">
              IRA
            </th>
            <th className="px-3 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider border-r border-gray-200 min-w-[140px]">
              Per Partner Income Threshold
            </th>
            <th className="px-3 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider min-w-[140px]">
              Per Partner W/H Tax Threshold
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {data.map((stateData, index) => (
            <tr key={stateData.stateCode} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
              <td className="px-3 py-3 whitespace-nowrap text-sm text-gray-900 border-r border-gray-200 font-medium">
                {stateData.state}
              </td>
              <td className="px-3 py-3 whitespace-nowrap text-sm text-gray-900 border-r border-gray-200 font-medium">
                {stateData.stateCode}
              </td>
              <td className="px-3 py-3 whitespace-nowrap text-sm text-gray-900 border-r border-gray-200 text-center">
                {(stateData.individual * 100).toFixed(2)}%
              </td>
              <td className="px-3 py-3 whitespace-nowrap text-sm text-gray-900 border-r border-gray-200 text-center">
                {(stateData.estate * 100).toFixed(2)}%
              </td>
              <td className="px-3 py-3 whitespace-nowrap text-sm text-gray-900 border-r border-gray-200 text-center">
                {(stateData.trust * 100).toFixed(2)}%
              </td>
              <td className="px-3 py-3 whitespace-nowrap text-sm text-gray-900 border-r border-gray-200 text-center">
                {(stateData.partnership * 100).toFixed(2)}%
              </td>
              <td className="px-3 py-3 whitespace-nowrap text-sm text-gray-900 border-r border-gray-200 text-center">
                {(stateData.sCorporation * 100).toFixed(2)}%
              </td>
              <td className="px-3 py-3 whitespace-nowrap text-sm text-gray-900 border-r border-gray-200 text-center">
                {(stateData.corporation * 100).toFixed(2)}%
              </td>
              <td className="px-3 py-3 whitespace-nowrap text-sm text-gray-900 border-r border-gray-200 text-center">
                {(stateData.exemptOrg * 100).toFixed(2)}%
              </td>
              <td className="px-3 py-3 whitespace-nowrap text-sm text-gray-900 border-r border-gray-200 text-center">
                {(stateData.ira * 100).toFixed(2)}%
              </td>
              <td className="px-3 py-3 whitespace-nowrap text-sm text-gray-900 border-r border-gray-200 text-center">
                ${stateData.incomeThreshold.toLocaleString()}
              </td>
              <td className="px-3 py-3 whitespace-nowrap text-sm text-gray-900 text-center">
                ${stateData.taxThreshold.toLocaleString()}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// Composite Rules Table Component
function CompositeRulesTable({ data }: { data: StateCompositeData[] }) {
  if (data.length === 0) {
    return (
      <div className="p-6 text-center text-gray-500">
        No composite rules found for this rule set.
      </div>
    );
  }

  return (
    <div className="overflow-x-auto overflow-y-auto max-h-[60vh] w-full">
      <table className="w-full divide-y divide-gray-200 border border-gray-200" style={{ minWidth: '1400px' }}>
        <thead className="bg-gray-50 sticky top-0">
          <tr>
            <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-r border-gray-200 min-w-[120px]">
              State
            </th>
            <th className="px-3 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider border-r border-gray-200 min-w-[80px]">
              State Abbrev
            </th>
            <th className="px-3 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider border-r border-gray-200 min-w-[90px]">
              Individual
            </th>
            <th className="px-3 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider border-r border-gray-200 min-w-[80px]">
              Estate
            </th>
            <th className="px-3 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider border-r border-gray-200 min-w-[80px]">
              Trust
            </th>
            <th className="px-3 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider border-r border-gray-200 min-w-[100px]">
              Partnership
            </th>
            <th className="px-3 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider border-r border-gray-200 min-w-[110px]">
              S Corporation
            </th>
            <th className="px-3 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider border-r border-gray-200 min-w-[100px]">
              Corporation
            </th>
            <th className="px-3 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider border-r border-gray-200 min-w-[100px]">
              Exempt Org
            </th>
            <th className="px-3 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider border-r border-gray-200 min-w-[70px]">
              IRA
            </th>
            <th className="px-3 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider border-r border-gray-200 min-w-[120px]">
              Income Threshold
            </th>
            <th className="px-3 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider min-w-[100px]">
              Mandatory
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {data.map((stateData, index) => (
            <tr key={stateData.stateCode} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
              <td className="px-3 py-3 whitespace-nowrap text-sm text-gray-900 border-r border-gray-200 font-medium">
                {stateData.state}
              </td>
              <td className="px-3 py-3 whitespace-nowrap text-sm text-gray-900 border-r border-gray-200 font-medium">
                {stateData.stateCode}
              </td>
              <td className="px-3 py-3 whitespace-nowrap text-sm text-gray-900 border-r border-gray-200 text-center">
                {(stateData.individual * 100).toFixed(2)}%
              </td>
              <td className="px-3 py-3 whitespace-nowrap text-sm text-gray-900 border-r border-gray-200 text-center">
                {(stateData.estate * 100).toFixed(2)}%
              </td>
              <td className="px-3 py-3 whitespace-nowrap text-sm text-gray-900 border-r border-gray-200 text-center">
                {(stateData.trust * 100).toFixed(2)}%
              </td>
              <td className="px-3 py-3 whitespace-nowrap text-sm text-gray-900 border-r border-gray-200 text-center">
                {(stateData.partnership * 100).toFixed(2)}%
              </td>
              <td className="px-3 py-3 whitespace-nowrap text-sm text-gray-900 border-r border-gray-200 text-center">
                {(stateData.sCorporation * 100).toFixed(2)}%
              </td>
              <td className="px-3 py-3 whitespace-nowrap text-sm text-gray-900 border-r border-gray-200 text-center">
                {(stateData.corporation * 100).toFixed(2)}%
              </td>
              <td className="px-3 py-3 whitespace-nowrap text-sm text-gray-900 border-r border-gray-200 text-center">
                {(stateData.exemptOrg * 100).toFixed(2)}%
              </td>
              <td className="px-3 py-3 whitespace-nowrap text-sm text-gray-900 border-r border-gray-200 text-center">
                {(stateData.ira * 100).toFixed(2)}%
              </td>
              <td className="px-3 py-3 whitespace-nowrap text-sm text-gray-900 border-r border-gray-200 text-center">
                ${stateData.incomeThreshold.toLocaleString()}
              </td>
              <td className="px-3 py-3 whitespace-nowrap text-sm text-gray-900 text-center">
                {stateData.mandatory ? 'Mandatory' : ''}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}