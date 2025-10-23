import React, { useState } from 'react';
import { 
  Shield, 
  Download, 
  FileText, 
  Loader2, 
  CheckCircle, 
  AlertCircle,
  Settings,
  Eye,
  EyeOff
} from 'lucide-react';
import { RedactionControlsProps, RedactionMethod } from '../types';

const RedactionControls: React.FC<RedactionControlsProps> = ({
  detection,
  onRedact,
  isRedacting,
  redactionResult,
}) => {
  const [selectedMethod, setSelectedMethod] = useState<RedactionMethod>('blur');
  const [showAdvanced, setShowAdvanced] = useState(false);

  const redactionMethods = [
    {
      value: 'blur' as RedactionMethod,
      label: 'Blur',
      description: 'Apply Gaussian blur to sensitive areas',
      icon: EyeOff,
    },
    {
      value: 'blackbox' as RedactionMethod,
      label: 'Black Box',
      description: 'Cover with solid black rectangles',
      icon: Shield,
    },
    {
      value: 'pixelate' as RedactionMethod,
      label: 'Pixelate',
      description: 'Apply pixelation effect',
      icon: Eye,
    },
  ];

  const handleRedact = () => {
    if (detection && !isRedacting) {
      onRedact(selectedMethod);
    }
  };

  const downloadFile = async (url: string, filename: string) => {
    try {
      const response = await fetch(`http://localhost:8000${url}`);
      const blob = await response.blob();
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(downloadUrl);
    } catch (error) {
      console.error('Download failed:', error);
    }
  };

  if (!detection) {
    return null;
  }

  const { detection_summary } = detection;
  const hasPII = detection_summary.total_pii_found > 0;

  return (
    <div className="space-y-6">
      {/* Redaction Method Selection */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Redaction Settings</h3>
          <button
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="flex items-center space-x-2 text-sm text-gray-600 hover:text-gray-900"
          >
            <Settings className="w-4 h-4" />
            <span>{showAdvanced ? 'Hide' : 'Show'} Advanced</span>
          </button>
        </div>

        <div className="space-y-4">
          <div>
            <label className="text-sm font-medium text-gray-700 mb-3 block">
              Redaction Method
            </label>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {redactionMethods.map((method) => (
                <button
                  key={method.value}
                  onClick={() => setSelectedMethod(method.value)}
                  disabled={isRedacting}
                  className={`
                    p-4 rounded-lg border-2 text-left transition-all duration-200
                    ${selectedMethod === method.value
                      ? 'border-primary-500 bg-primary-50 ring-2 ring-primary-200'
                      : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                    }
                    ${isRedacting ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
                  `}
                >
                  <div className="flex items-start space-x-3">
                    <method.icon className={`w-5 h-5 mt-0.5 ${
                      selectedMethod === method.value ? 'text-primary-600' : 'text-gray-400'
                    }`} />
                    <div>
                      <div className={`font-medium ${
                        selectedMethod === method.value ? 'text-primary-900' : 'text-gray-900'
                      }`}>
                        {method.label}
                      </div>
                      <div className={`text-sm ${
                        selectedMethod === method.value ? 'text-primary-700' : 'text-gray-600'
                      }`}>
                        {method.description}
                      </div>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </div>

          {showAdvanced && (
            <div className="pt-4 border-t border-gray-200">
              <div className="text-sm text-gray-600">
                <p className="mb-2">
                  <strong>Confidence Threshold:</strong> {detection_summary.confidence_score 
                    ? `${Math.round((detection_summary.confidence_score || 0) * 100)}%`
                    : 'Default (70%)'
                  }
                </p>
                <p>
                  <strong>Detection Quality:</strong> {detection_summary.confidence_score 
                    ? detection_summary.confidence_score > 0.8 ? 'High' 
                      : detection_summary.confidence_score > 0.6 ? 'Medium' : 'Low'
                    : 'Unknown'
                  }
                </p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Redaction Action */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Redaction Process</h3>
          {hasPII && (
            <div className="flex items-center space-x-2 text-sm text-warning-600">
              <AlertCircle className="w-4 h-4" />
              <span>{detection_summary.total_pii_found} entities will be redacted</span>
            </div>
          )}
        </div>

        {!hasPII ? (
          <div className="space-y-4">
            <div className="p-4 bg-success-50 border border-success-200 rounded-lg">
              <div className="flex items-start space-x-3">
                <CheckCircle className="w-5 h-5 text-success-500 mt-0.5 flex-shrink-0" />
                <div>
                  <h4 className="text-sm font-medium text-success-800">No PII Detected</h4>
                  <p className="text-sm text-success-700 mt-1">
                    This document appears to be clean of personally identifiable information. 
                    You can still process it to create a redacted version or run additional checks.
                  </p>
                </div>
              </div>
            </div>

            <button
              onClick={handleRedact}
              disabled={isRedacting}
              className={`
                w-full flex items-center justify-center space-x-3 px-6 py-3 rounded-lg font-medium transition-all duration-200
                ${isRedacting
                  ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                  : 'bg-primary-600 hover:bg-primary-700 text-white shadow-lg hover:shadow-xl'
                }
              `}
            >
              {isRedacting ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  <span>Processing Document...</span>
                </>
              ) : (
                <>
                  <Shield className="w-5 h-5" />
                  <span>Process Document (No PII Found)</span>
                </>
              )}
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="p-4 bg-warning-50 border border-warning-200 rounded-lg">
              <div className="flex items-start space-x-3">
                <AlertCircle className="w-5 h-5 text-warning-500 mt-0.5 flex-shrink-0" />
                <div>
                  <h4 className="text-sm font-medium text-warning-800">Ready to Redact</h4>
                  <p className="text-sm text-warning-700 mt-1">
                    The following PII will be redacted using the {selectedMethod} method:
                  </p>
                  <ul className="text-xs text-warning-600 mt-2 space-y-1">
                    {detection_summary.breakdown.emails > 0 && (
                      <li>• {detection_summary.breakdown.emails} email address(es)</li>
                    )}
                    {detection_summary.breakdown.phone_numbers > 0 && (
                      <li>• {detection_summary.breakdown.phone_numbers} phone number(s)</li>
                    )}
                    {detection_summary.breakdown.identifiers > 0 && (
                      <li>• {detection_summary.breakdown.identifiers} identifier(s)</li>
                    )}
                    {detection_summary.breakdown.addresses > 0 && (
                      <li>• {detection_summary.breakdown.addresses} address(es)</li>
                    )}
                  </ul>
                </div>
              </div>
            </div>

            <button
              onClick={handleRedact}
              disabled={isRedacting}
              className={`
                w-full flex items-center justify-center space-x-3 px-6 py-3 rounded-lg font-medium transition-all duration-200
                ${isRedacting
                  ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                  : 'bg-primary-600 hover:bg-primary-700 text-white shadow-lg hover:shadow-xl'
                }
              `}
            >
              {isRedacting ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  <span>Redacting Document...</span>
                </>
              ) : (
                <>
                  <Shield className="w-5 h-5" />
                  <span>Start Redaction</span>
                </>
              )}
            </button>
          </div>
        )}
      </div>

      {/* Redaction Results */}
      {redactionResult && (
        <div className="bg-white rounded-xl border border-success-200 p-6">
          <div className="flex items-center space-x-3 mb-4">
            <CheckCircle className="w-6 h-6 text-success-500" />
            <h3 className="text-lg font-semibold text-success-800">Redaction Complete</h3>
          </div>

          <div className="space-y-4">
            <div className="p-4 bg-success-50 border border-success-200 rounded-lg">
              <div className="text-sm text-success-800">
                <p className="font-medium mb-2">Redaction Summary:</p>
                <ul className="space-y-1">
                  <li>• Method: {redactionResult.redaction_method}</li>
                  <li>• Entities redacted: {redactionResult.redaction_summary.total_entities_redacted}</li>
                  <li>• Output file: {redactionResult.redacted_file}</li>
                </ul>
              </div>
            </div>

            <div className="flex flex-col sm:flex-row gap-3">
              <button
                onClick={() => downloadFile(redactionResult.download_url, redactionResult.redacted_file)}
                className="flex items-center justify-center space-x-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
              >
                <Download className="w-4 h-4" />
                <span>Download Redacted File</span>
              </button>
              
              <button
                onClick={() => downloadFile(redactionResult.report_url, redactionResult.report_used)}
                className="flex items-center justify-center space-x-2 px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
              >
                <FileText className="w-4 h-4" />
                <span>Download Report</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default RedactionControls;
