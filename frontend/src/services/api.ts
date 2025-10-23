import axios from 'axios';

const API_BASE_URL = 'http://127.0.0.1:8000';


const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 90000, // 30 seconds timeout for file processing
});

// Request interceptor for logging
api.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('API Request Error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    console.log(`API Response: ${response.status} ${response.config.url}`);
    return response;
  },
  (error) => {
    console.error('API Response Error:', error);
    if (error.response) {
      // Server responded with error status
      const message = error.response.data?.detail || error.response.data?.message || 'An error occurred';
      throw new Error(message);
    } else if (error.request) {
      // Request was made but no response received
      throw new Error('Network error: Unable to connect to the server');
    } else {
      // Something else happened
      throw new Error(error.message || 'An unexpected error occurred');
    }
  }
);

export interface PIIDetectionRequest {
  file: File;
}

export interface PIIDetectionResponse {
  status: string;
  scan_id: string;
  timestamp: string;
  input_file: string;
  uploaded_as: string;
  report_file: string;
  detection_summary: {
    total_pii_found: number;
    breakdown: {
      emails: number;
      phone_numbers: number;
      identifiers: number;
      addresses: number;
    };
    pii_class: string;
    confidence_score: number;
    country_of_origin: string;
    contains_faces: boolean;
  };
  detected_pii: {
    emails: any[];
    phone_numbers: any[];
    identifiers: any[];
    addresses: any[];
  };
  pii_locations: Record<string, any>;
  full_report: any;
}

export interface RedactionRequest {
  file: File;
  report_filename?: string;
  method: 'blur' | 'blackbox' | 'pixelate';
}

export interface RedactionResponse {
  status: string;
  redact_id: string;
  timestamp: string;
  input_file: string;
  redacted_file: string;
  report_used: string;
  redaction_method: string;
  redaction_summary: {
    total_entities_redacted: number;
    breakdown: {
      emails: number;
      phone_numbers: number;
      identifiers: number;
      addresses: number;
    };
  };
  download_url: string;
  report_url: string;
}

export const piiApi = {
  // Detect PII in uploaded file
  detectPII: async (file: File): Promise<PIIDetectionResponse> => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await api.post('/detect-pii/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    return response.data;
  },

  // Redact PII from uploaded file
  redactPII: async (file: File, reportFilename: string, method: 'blur' | 'blackbox' | 'pixelate'): Promise<RedactionResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('report_filename', reportFilename);
    formData.append('method', method);

    const response = await api.post('/redact-pii/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    return response.data;
  },

  // Download redacted file
  downloadRedactedFile: (filename: string): string => {
    return `${API_BASE_URL}/download-redacted/${filename}`;
  },

  // Download detection report
  downloadReport: (filename: string): string => {
    return `${API_BASE_URL}/download-report/${filename}`;
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

export default api;
