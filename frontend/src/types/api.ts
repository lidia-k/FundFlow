export interface UploadResponse {
  session_id: string;
  filename: string;
  status: CalculationStatus;
  message: string;
  created_at: string;
}

export interface PortfolioCompany {
  name: string;
  state: string;
  revenue: number;
  tax_allocation: Record<string, number>;
}

export interface LPAllocation {
  lp_name: string;
  ownership_percentage: number;
  salt_allocation: Record<string, number>;
  total_allocation: number;
}

export interface CalculationResult {
  session_id: string;
  filename: string;
  status: CalculationStatus;
  portfolio_companies: PortfolioCompany[];
  lp_allocations: LPAllocation[];
  total_salt_amount: number;
  calculation_summary: Record<string, any>;
  created_at: string;
  completed_at?: string;
}

export interface SessionInfo {
  session_id: string;
  filename: string;
  status: CalculationStatus;
  created_at: string;
  completed_at?: string;
}

export type CalculationStatus = 'pending' | 'processing' | 'completed' | 'failed';

export interface ErrorResponse {
  detail: string;
  error_code?: string;
}

export interface ResultsPreviewRow {
  investor_name: string;
  entity_type: string;
  tax_state: string;
  jurisdiction: string;
  amount: number;
  fund_code: string;
  period: string;
  composite_exemption?: string;
  withholding_exemption?: string;
  composite_tax_amount?: number | null;
  withholding_tax_amount?: number | null;
}

export interface ResultsPreviewResponse {
  session_id: string;
  status: CalculationStatus;
  preview_data: ResultsPreviewRow[];
  total_records: number;
  preview_limit: number;
  showing_count: number;
}
