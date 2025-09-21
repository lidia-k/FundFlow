// Frontend TypeScript interfaces for Epic 2B Tax Calculation

export interface DistributionWithTaxes {
  id: number;
  investor_name: string;
  jurisdiction: string;
  amount: number;

  // Legacy exemption flags (preserved for backward compatibility)
  composite_exemption: boolean;
  withholding_exemption: boolean;

  // Tax calculation results
  withholding_tax_tx?: number | null;
  withholding_tax_nm?: number | null;
  withholding_tax_co?: number | null;
  composite_tax_tx?: number | null;
  composite_tax_nm?: number | null;
  composite_tax_co?: number | null;

  // Calculation metadata
  tax_calculation_applied: boolean;
  exemption_reason?: string | null;
  calculation_timestamp?: string | null;
}

export interface TaxCalculationSummary {
  session_id: string;
  salt_rule_set_id?: number | null;
  salt_rule_set_name?: string | null;
  total_distributions: number;
  distributions_with_taxes: number;
  distributions_exempted: number;

  // Tax totals by state
  total_withholding_tax_tx: number;
  total_withholding_tax_nm: number;
  total_withholding_tax_co: number;
  total_composite_tax_tx: number;
  total_composite_tax_nm: number;
  total_composite_tax_co: number;

  calculation_timestamp: string;
}

export interface SessionWithTaxCalculations {
  session_id: string;
  user_id: number;
  filename: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  created_at: string;
  has_tax_calculations: boolean;
  tax_calculation_summary?: TaxCalculationSummary | null;
  distributions: DistributionWithTaxes[];
}

export interface TaxCalculationAuditDetail {
  distribution_id: number;
  investor_name: string;
  jurisdiction: string;
  distribution_amount: number;

  // Step 1: Exemption checks
  step1_exemption_applied: boolean;
  step1_exemption_reason?: string | null;
  step1_jurisdiction_matches_tax_state: boolean;

  // Step 2: Composite tax calculation
  step2_mandatory_filing_required: boolean;
  step2_composite_tax_calculated: boolean;
  step2_tax_rate?: number | null;
  step2_tax_amount?: number | null;

  // Step 3: Withholding tax calculation
  step3_withholding_tax_calculated: boolean;
  step3_tax_rate?: number | null;
  step3_tax_amount?: number | null;

  applied_rules: AppliedTaxRules;
  calculation_timestamp: string;
}

export interface AppliedTaxRules {
  composite_rule?: {
    rule_id: number;
    state: string;
    entity_type: string;
    tax_rate: number;
    mandatory_filing: boolean;
    income_threshold?: number | null;
  } | null;
  withholding_rule?: {
    rule_id: number;
    state: string;
    entity_type: string;
    tax_rate: number;
    per_partner_income_threshold?: number | null;
    per_partner_wh_tax_threshold?: number | null;
  } | null;
}

export interface TaxCalculationAuditReport {
  session_id: string;
  report_generated_at: string;
  salt_rule_set_used: SaltRuleSetInfo;
  summary: TaxCalculationSummary;
  calculation_details: TaxCalculationAuditDetail[];
}

export interface SaltRuleSetInfo {
  id: number;
  name: string;
  version: string;
  status: 'active' | 'draft' | 'archived';
  effective_date: string;
  created_at: string;
}

// Component Props Interfaces

export interface TaxResultsTableProps {
  distributions: DistributionWithTaxes[];
  hasTaxCalculations: boolean;
  loading?: boolean;
}

export interface TaxSummaryCardProps {
  summary: TaxCalculationSummary;
  onDownloadAuditReport: () => void;
}

export interface ResultsModalWithTaxesProps {
  isOpen: boolean;
  onClose: () => void;
  session: SessionWithTaxCalculations;
  onDownloadResults: () => void;
  onDownloadAuditReport?: () => void;
}

// Column Definition Types for Data Grid

export interface TaxColumnDefinition {
  key: string;
  label: string;
  type: 'currency' | 'text' | 'boolean' | 'date';
  precision?: number; // For currency columns
  conditional?: boolean; // Show only when tax calculations applied
  exemptionFallback?: string; // Fallback column for non-tax sessions
}

export interface DynamicColumnConfig {
  baseColumns: TaxColumnDefinition[];
  taxColumns: TaxColumnDefinition[];
  exemptionColumns: TaxColumnDefinition[];
}

// API Response Types

export interface GetSessionWithTaxesResponse {
  data: SessionWithTaxCalculations;
  success: boolean;
  message?: string;
}

export interface GetAuditReportResponse {
  data: TaxCalculationAuditReport;
  success: boolean;
  message?: string;
}

export interface DownloadAuditReportResponse {
  blob: Blob;
  filename: string;
}

// Utility Types

export type TaxAmountFields =
  | 'withholding_tax_tx'
  | 'withholding_tax_nm'
  | 'withholding_tax_co'
  | 'composite_tax_tx'
  | 'composite_tax_nm'
  | 'composite_tax_co';

export type StateCode = 'TX' | 'NM' | 'CO';

export interface TaxAmountsByState {
  withholding: Record<StateCode, number>;
  composite: Record<StateCode, number>;
}

// Form Validation Types

export interface TaxCalculationValidation {
  hasActiveSaltRules: boolean;
  canCalculateTaxes: boolean;
  validationErrors: string[];
  warnings: string[];
}

// Error Types

export interface TaxCalculationError {
  type: 'exemption' | 'calculation' | 'rule_missing' | 'threshold' | 'system';
  message: string;
  distribution_id?: number;
  investor_name?: string;
  jurisdiction?: string;
  details?: Record<string, any>;
}

export interface TaxCalculationErrorResponse {
  error: string;
  message: string;
  details?: {
    calculation_errors: TaxCalculationError[];
    affected_distributions: number[];
  };
}