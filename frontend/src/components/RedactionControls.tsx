import React, { useState } from "react";
import {
  RedactionControlsProps,
  RedactionMethod,
  RedactionResult,
} from "../types";
import {
  Shield,
  Download,
  Settings,
  FileText,
  Image,
  Palette,
  Loader2,
} from "lucide-react";
import { piiApi } from "../services/api";

const RedactionControls: React.FC<RedactionControlsProps> = ({
  detectionResult,
  selectedFile,
  redactionMethod,
  onMethodChange,
  onRedactionComplete,
  onLoading,
}) => {
  const [isRedacting, setIsRedacting] = useState(false);
  const [redactionResult, setRedactionResult] = useState<any>(null);

  const redactionMethods: {
    value: RedactionMethod;
    label: string;
    description: string;
    icon: React.ReactNode;
  }[] = [
    {
      value: "blur",
      label: "Blur",
      description: "Apply Gaussian blur to sensitive areas",
      icon: <Image className="w-5 h-5" />,
    },
    {
      value: "blackbox",
      label: "Black Box",
      description: "Cover with solid black rectangles",
      icon: <Shield className="w-5 h-5" />,
    },
    {
      value: "pixelate",
      label: "Pixelate",
      description: "Apply pixelation effect to sensitive areas",
      icon: <Palette className="w-5 h-5" />,
    },
  ];

  const handleRedaction = async () => {
    if (!detectionResult) return;

    setIsRedacting(true);
    onLoading(true);

    try {
      // Use the original uploaded file if available. The backend expects a
      // valid PDF/image file; creating an empty placeholder previously caused
      // the "File does not appear to be a valid PDF" error.
      if (!selectedFile) {
        throw new Error(
          "Original uploaded file is not available. Please re-upload the file before redaction."
        );
      }

      const result = await piiApi.redactPII(
        selectedFile,
        detectionResult.report_file,
        redactionMethod
      );

      setRedactionResult(result);
      onRedactionComplete(result as RedactionResult);
    } catch (error) {
      console.error("Redaction error:", error);
      alert(
        error instanceof Error
          ? error.message
          : "An error occurred during redaction"
      );
    } finally {
      setIsRedacting(false);
      onLoading(false);
    }
  };

  const downloadRedactedFile = () => {
    if (redactionResult?.redacted_file) {
      const link = document.createElement("a");
      link.href = piiApi.downloadRedactedFile(redactionResult.redacted_file);
      link.download = `redacted_${detectionResult.input_file}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  };

  const downloadReport = () => {
    if (detectionResult?.report_file) {
      const link = document.createElement("a");
      link.href = piiApi.downloadReport(detectionResult.report_file);
      link.download = detectionResult.report_file;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  };

  return (
    <div className="space-y-6">
      {/* Redaction Method Selection */}
      <div className="card">
        <div className="flex items-center space-x-2 mb-4">
          <Settings className="w-5 h-5 text-gray-600" />
          <h3 className="text-lg font-semibold text-gray-900">
            Redaction Settings
          </h3>
        </div>

        <div className="space-y-3">
          <label className="block text-sm font-medium text-gray-700">
            Redaction Method
          </label>
          <div className="space-y-2">
            {redactionMethods.map((method) => (
              <label
                key={method.value}
                className={`flex items-center p-3 border rounded-lg cursor-pointer transition-colors ${
                  redactionMethod === method.value
                    ? "border-primary-500 bg-primary-50"
                    : "border-gray-200 hover:border-gray-300"
                }`}
              >
                <input
                  type="radio"
                  name="redactionMethod"
                  value={method.value}
                  checked={redactionMethod === method.value}
                  onChange={(e) =>
                    onMethodChange(e.target.value as RedactionMethod)
                  }
                  className="sr-only"
                />
                <div className="flex items-center space-x-3 flex-1">
                  <div
                    className={`p-2 rounded-lg ${
                      redactionMethod === method.value
                        ? "text-primary-600 bg-primary-100"
                        : "text-gray-400 bg-gray-100"
                    }`}
                  >
                    {method.icon}
                  </div>
                  <div>
                    <div className="font-medium text-gray-900">
                      {method.label}
                    </div>
                    <div className="text-sm text-gray-500">
                      {method.description}
                    </div>
                  </div>
                </div>
                {redactionMethod === method.value && (
                  <div className="w-5 h-5 bg-primary-600 rounded-full flex items-center justify-center">
                    <div className="w-2 h-2 bg-white rounded-full"></div>
                  </div>
                )}
              </label>
            ))}
          </div>
        </div>
      </div>

      {/* Redaction Actions */}
      <div className="card">
        <div className="flex items-center space-x-2 mb-4">
          <Shield className="w-5 h-5 text-gray-600" />
          <h3 className="text-lg font-semibold text-gray-900">
            Redaction Actions
          </h3>
        </div>

        <div className="space-y-4">
          <button
            onClick={handleRedaction}
            disabled={
              isRedacting ||
              detectionResult.detection_summary.total_pii_found === 0
            }
            className="w-full btn-primary flex items-center justify-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isRedacting ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Redacting...</span>
              </>
            ) : (
              <>
                <Shield className="w-4 h-4" />
                <span>Start Redaction</span>
              </>
            )}
          </button>

          {detectionResult.detection_summary.total_pii_found === 0 && (
            <div className="text-center p-3 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-600">
                No PII detected. Redaction is not necessary.
              </p>
            </div>
          )}

          <div className="flex space-x-2">
            <button
              onClick={downloadReport}
              className="flex-1 btn-secondary flex items-center justify-center space-x-2"
            >
              <FileText className="w-4 h-4" />
              <span>Download Report</span>
            </button>

            {redactionResult && (
              <button
                onClick={downloadRedactedFile}
                className="flex-1 btn-primary flex items-center justify-center space-x-2"
              >
                <Download className="w-4 h-4" />
                <span>Download Redacted</span>
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Redaction Preview */}
      {redactionResult && (
        <div className="card border-success-200 bg-success-50">
          <div className="flex items-start space-x-3">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-success-100 rounded-full flex items-center justify-center">
                <Shield className="w-5 h-5 text-success-600" />
              </div>
            </div>
            <div className="flex-1">
              <h4 className="font-medium text-success-800">
                Redaction Complete
              </h4>
              <p className="text-sm text-success-700 mt-1">
                Successfully redacted{" "}
                {redactionResult.redaction_summary.total_entities_redacted} PII
                entities using {redactionResult.redaction_method} method.
              </p>
              <div className="mt-2 text-xs text-success-600">
                File: {redactionResult.redacted_file}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Statistics */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Redaction Statistics
        </h3>
        <div className="grid grid-cols-2 gap-4">
          <div className="text-center p-3 bg-gray-50 rounded-lg">
            <div className="text-2xl font-bold text-gray-900">
              {detectionResult.detection_summary.total_pii_found}
            </div>
            <div className="text-sm text-gray-600">Items to Redact</div>
          </div>
          <div className="text-center p-3 bg-gray-50 rounded-lg">
            <div className="text-2xl font-bold text-gray-900">
              {redactionResult?.redaction_summary.total_entities_redacted || 0}
            </div>
            <div className="text-sm text-gray-600">Items Redacted</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default RedactionControls;
