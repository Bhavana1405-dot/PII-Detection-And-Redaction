export interface PIIDetection {
  emails: string[];
  phone_numbers: string[];
  identifiers: string[];
  addresses: string[];
}

export interface PIISummary {
  total_pii_found: number;
  breakdown: {
    emails: number;
    phone_numbers: number;
    identifiers: number;
    addresses: number;
  };
  pii_class?: string;
  confidence_score?: number;
  country_of_origin?: string;
  contains_faces: boolean;
}

export interface DetectionResponse {
  status: string;
  scan_id: string;
  timestamp: string;
  input_file: string;
  uploaded_as: string;
  report_file: string;
  detection_summary: PIISummary;
  detected_pii: PIIDetection;
  pii_locations: Record<string, any>;
  full_report: any;
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

export interface FileUploadProps {
  onFileSelect: (file: File) => void;
  isProcessing: boolean;
  acceptedTypes?: string;
}

export interface PIIDisplayProps {
  detection: DetectionResponse | null;
  isLoading: boolean;
  error: string | null;
}

export interface RedactionControlsProps {
  detection: DetectionResponse | null;
  onRedact: (method: string) => void;
  isRedacting: boolean;
  redactionResult: RedactionResponse | null;
}

export type RedactionMethod = 'blur' | 'blackbox' | 'pixelate';
