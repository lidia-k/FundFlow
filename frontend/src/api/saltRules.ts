import axios from 'axios';
import type {
  RuleSet,
  ValidationResponse,
  RulePreview,
  PublishRequest,
  UploadResponse,
  SaltRulesListResponse
} from '../types/saltRules';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const saltRulesClient = axios.create({
  baseURL: `${API_BASE_URL}/api/salt-rules`,
  timeout: 60000, // 60 seconds for file uploads
});

// Request interceptor for logging
saltRulesClient.interceptors.request.use((config) => {
  console.log(`SALT Rules API Request: ${config.method?.toUpperCase()} ${config.url}`);
  return config;
});

// Response interceptor for error handling
saltRulesClient.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('SALT Rules API Error:', error.response?.data || error.message);
    throw error;
  }
);

export const saltRulesApi = {
  // Upload SALT rules Excel file
  upload: async (file: File): Promise<UploadResponse> => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await saltRulesClient.post<UploadResponse>('/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    return response.data;
  },


  // Get preview of changes before publishing
  getPreview: async (ruleSetId: string): Promise<RulePreview> => {
    const response = await saltRulesClient.get<RulePreview>(`/${ruleSetId}/preview`);
    return response.data;
  },

  // Publish rule set
  publish: async (ruleSetId: string, data: PublishRequest): Promise<{ message: string; publishedAt: string }> => {
    const response = await saltRulesClient.post(`/${ruleSetId}/publish`, data);
    return response.data;
  },

  // List all rule sets
  list: async (offset = 0, limit = 50): Promise<SaltRulesListResponse> => {
    const response = await saltRulesClient.get<SaltRulesListResponse>('', {
      params: { offset, limit }
    });
    return response.data;
  },

  // Get specific rule set details
  getDetails: async (ruleSetId: string): Promise<RuleSet> => {
    const response = await saltRulesClient.get<RuleSet>(`/${ruleSetId}`);
    return response.data;
  },

  // Download validation results as CSV
  downloadValidationResults: async (ruleSetId: string): Promise<Blob> => {
    const response = await saltRulesClient.get(`/${ruleSetId}/validation-export`, {
      responseType: 'blob',
    });
    return response.data;
  },

  // Delete rule set
  delete: async (ruleSetId: string): Promise<{ message: string; deletedAt: string }> => {
    const response = await saltRulesClient.delete(`/${ruleSetId}`);
    return response.data;
  },
};

export default saltRulesApi;