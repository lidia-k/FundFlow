export interface WithholdingRule {
  id: string;
  state: string;
  stateCode: string;
  entityType: string;
  taxRate: number;
  incomeThreshold: number;
  taxThreshold: number;
}

export interface CompositeRule {
  id: string;
  state: string;
  stateCode: string;
  entityType: string;
  taxRate: number;
  incomeThreshold: number;
  mandatoryFiling: boolean;
}

export interface StateWithholdingData {
  state: string;
  stateCode: string;
  individual: number;
  estate: number;
  trust: number;
  partnership: number;
  sCorporation: number;
  corporation: number;
  exemptOrg: number;
  ira: number;
  incomeThreshold: number;
  taxThreshold: number;
}

export interface StateCompositeData {
  state: string;
  stateCode: string;
  individual: number;
  estate: number;
  trust: number;
  partnership: number;
  sCorporation: number;
  corporation: number;
  exemptOrg: number;
  ira: number;
  incomeThreshold: number;
  mandatory: boolean;
}

export interface RuleSet {
  id: string;
  status: RuleSetStatus;
  version: string;
  quarter: string;
  year: number;
  effectiveDate: string;
  createdAt: string;
  publishedAt?: string;
  ruleCountWithholding: number;
  ruleCountComposite: number;
  description?: string;
  withholdingRules?: WithholdingRule[];
  compositeRules?: CompositeRule[];
}

export type RuleSetStatus = 'draft' | 'active' | 'archived';

export interface ValidationIssue {
  id: string;
  ruleSetId: string;
  severity: 'error' | 'warning' | 'info';
  message: string;
  rowNumber?: number;
  column?: string;
  context?: Record<string, any>;
}

export interface ValidationResponse {
  ruleSetId: string;
  status: RuleSetStatus;
  summary: {
    totalRules: number;
    validRules: number;
    errorCount: number;
    warningCount: number;
    processingTime: number;
  };
  issues: ValidationIssue[];
}


export interface ValidationError {
  sheet: string;
  row: number;
  column?: string;
  error_code: string;
  message: string;
  field_value?: any;
}

export interface UploadResponse {
  ruleSetId: string;
  status: 'valid' | 'validation_failed';
  uploadedFile: {
    filename: string;
    fileSize: number;
    uploadTimestamp: string;
  };
  validationStarted: boolean;
  message: string;
  validationErrors?: ValidationError[];
  ruleCounts?: {
    withholding: number;
    composite: number;
  };
}

export interface SaltRulesListResponse {
  items: RuleSet[];
  totalCount: number;
  offset: number;
  limit: number;
  hasMore: boolean;
}