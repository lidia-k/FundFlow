import axios from 'axios';
import type {
  UploadResponse,
  CalculationResult,
  SessionInfo,
  ResultsPreviewResponse,
} from '../types/api';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: `${API_BASE_URL}/api`,
  timeout: 60000, // 60 seconds for file uploads
});

// Request interceptor for logging
apiClient.interceptors.request.use((config) => {
  console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
  return config;
});

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    throw error;
  }
);

export const api = {
  // Upload file and start calculation
  uploadFile: async (file: File): Promise<UploadResponse> => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await apiClient.post<UploadResponse>('/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    return response.data;
  },

  // Get calculation results
  getResults: async (sessionId: string): Promise<CalculationResult> => {
    const response = await apiClient.get<CalculationResult>(`/results/${sessionId}`);
    return response.data;
  },

  // Get preview of calculation results
  getResultsPreview: async (
    sessionId: string,
    limit: number = 100,
    mode: 'upload' | 'results' = 'upload',
  ): Promise<ResultsPreviewResponse> => {
    const response = await apiClient.get<ResultsPreviewResponse>(
      `/results/${sessionId}/preview?limit=${limit}&mode=${mode}`
    );
    return response.data;
  },


  // Download results file
  downloadResults: async (sessionId: string): Promise<Blob> => {
    const response = await apiClient.get(`/results/${sessionId}/download`, {
      responseType: 'blob',
    });
    return response.data;
  },

  // Download detailed tax calculation report
  downloadTaxReport: async (sessionId: string): Promise<Blob> => {
    const response = await apiClient.get(`/results/${sessionId}/report`, {
      responseType: 'blob',
    });
    return response.data;
  },

  // Get all sessions
  getSessions: async (): Promise<SessionInfo[]> => {
    const response = await apiClient.get<SessionInfo[]>('/sessions');
    return response.data;
  },

  // Delete a session
  deleteSession: async (sessionId: string): Promise<{ message: string }> => {
    const response = await apiClient.delete<{ message: string }>(`/sessions/${sessionId}`);
    return response.data;
  },

  // Download template
  downloadTemplate: async (): Promise<Blob> => {
    const response = await apiClient.get('/template', {
      responseType: 'blob',
    });
    return response.data;
  },

  // Health check
  healthCheck: async (): Promise<{ status: string; version: string }> => {
    const response = await axios.get(`${API_BASE_URL}/health`);
    return response.data;
  },
};

export default api;
