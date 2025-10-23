import axios from 'axios';
import { DetectionResponse, RedactionResponse } from '../types';

const API_BASE_URL = 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 90000, // 30 seconds timeout for file processing
});

export const apiService = {
  // Detect PII in uploaded file
  detectPII: async (file: File): Promise<DetectionResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await api.post('/detect-pii/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    
    return response.data;
  },

  // Redact PII from file
  redactPII: async (
    file: File, 
    reportFilename?: string, 
    method: string = 'blur'
  ): Promise<RedactionResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    if (reportFilename) {
      formData.append('report_filename', reportFilename);
    }
    formData.append('method', method);
    
    const response = await api.post('/redact-pii/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    
    return response.data;
  },

  // Download redacted file
  downloadRedacted: async (filename: string): Promise<Blob> => {
    const response = await api.get(`/download-redacted/${filename}`, {
      responseType: 'blob',
    });
    
    return response.data;
  },

  // Download detection report
  downloadReport: async (filename: string): Promise<Blob> => {
    const response = await api.get(`/download-report/${filename}`, {
      responseType: 'blob',
    });
    
    return response.data;
  },

  // List all outputs
  listOutputs: async () => {
    const response = await api.get('/list-outputs/');
    return response.data;
  },

  // Health check
  healthCheck: async () => {
    const response = await api.get('/');
    return response.data;
  },
};

export default apiService;
