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