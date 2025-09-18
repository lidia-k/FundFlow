export interface RuleSet {
  ruleSetId: string;
  status: RuleSetStatus;
  filename: string;
  fileSize: number;
  sha256Hash: string;
  uploadedAt: string;
  publishedAt?: string;
  ruleCountWithholding: number;
  ruleCountComposite: number;
  version?: string;
  quarter?: string;
  year?: number;
  effectiveDate?: string;
  description?: string;
  archivedPrevious?: boolean;
  resolvedRulesGenerated?: boolean;
}

export type RuleSetStatus = 'uploaded' | 'validated' | 'published' | 'failed';

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

export interface RulePreview {
  ruleSetId: string;
  changes: {
    added: number;
    modified: number;
    removed: number;
  };
  preview: {
    addedRules: PreviewRule[];
    modifiedRules: PreviewRule[];
    removedRules: PreviewRule[];
  };
}

export interface PreviewRule {
  id: string;
  state: string;
  entity: string;
  taxType: string;
  rate: number;
  description?: string;
  effectiveDate?: string;
}

export interface PublishRequest {
  effectiveDate?: string;
  confirmArchive: boolean;
}

export interface UploadResponse {
  ruleSetId: string;
  status: RuleSetStatus;
  uploadedFile: {
    filename: string;
    fileSize: number;
    sha256Hash: string;
    uploadTimestamp: string;
  };
  validationStarted: boolean;
  message: string;
}

export interface SaltRulesListResponse {
  items: RuleSet[];
  totalCount: number;
  offset: number;
  limit: number;
  hasMore: boolean;
}