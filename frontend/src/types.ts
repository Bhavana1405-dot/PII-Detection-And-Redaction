export interface PIIDetectionResult {
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
    emails: PIIEntity[];
    phone_numbers: PIIEntity[];
    identifiers: PIIEntity[];
    addresses: PIIEntity[];
  };
  pii_locations: Record<string, any>;
  full_report: any;
}

export interface PIIEntity {
  value: string;
  confidence: number;
  location?: {
    page?: number;
    bbox?: [number, number, number, number];
    text_offset?: [number, number];
  };
  type?: string;
}

export type RedactionMethod = "blur" | "blackbox" | "pixelate";

export interface RedactionResult {
  status: string;
  redact_id: string;
  timestamp: string;
  input_file: string;
  redacted_file: string;
  report_used: string;
  redaction_method: RedactionMethod;
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
  // now also returns the original File so downstream components can re-use it for redaction
  onDetectionComplete: (result: PIIDetectionResult, file: File) => void;
  onError: (error: string) => void;
  onLoading: (loading: boolean) => void;
}

export interface DetectionResultsProps {
  result: PIIDetectionResult;
}

export interface RedactionControlsProps {
  detectionResult: PIIDetectionResult;
  // original uploaded file (required to submit to redaction API)
  selectedFile?: File;
  redactionMethod: RedactionMethod;
  onMethodChange: (method: RedactionMethod) => void;
  onRedactionComplete: (result: RedactionResult) => void;
  onLoading: (loading: boolean) => void;
}
