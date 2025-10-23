import React from 'react';
import { 
  Mail, 
  Phone, 
  CreditCard, 
  MapPin, 
  Eye, 
  AlertTriangle, 
  CheckCircle, 
  Loader2,
  XCircle
} from 'lucide-react';
import { PIIDisplayProps } from '../types';

const PIIDisplay: React.FC<PIIDisplayProps> = ({ detection, isLoading, error }) => {
  if (isLoading) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <div className="flex items-center justify-center space-x-3">
          <Loader2 className="w-6 h-6 text-primary-500 animate-spin" />
          <span className="text-gray-600">Analyzing document for PII...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-xl border border-danger-200 p-6">
        <div className="flex items-start space-x-3">
          <XCircle className="w-6 h-6 text-danger-500 mt-0.5 flex-shrink-0" />
          <div>
            <h3 className="text-lg font-semibold text-danger-800">Analysis Failed</h3>
            <p className="text-danger-600 mt-1">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  if (!detection) {
    return null;
  }

  const { detection_summary, detected_pii } = detection;
  const { total_pii_found, breakdown, confidence_score, contains_faces } = detection_summary;

  const piiTypes = [
    {
      key: 'emails',
      label: 'Email Addresses',
      icon: Mail,
      count: breakdown.emails,
      items: detected_pii.emails,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50',
      borderColor: 'border-blue-200',
    },
    {
      key: 'phone_numbers',
      label: 'Phone Numbers',
      icon: Phone,
      count: breakdown.phone_numbers,
      items: detected_pii.phone_numbers,
      color: 'text-green-600',
      bgColor: 'bg-green-50',
      borderColor: 'border-green-200',
    },
    {
      key: 'identifiers',
      label: 'Identifiers',
      icon: CreditCard,
      count: breakdown.identifiers,
      items: detected_pii.identifiers,
      color: 'text-purple-600',
      bgColor: 'bg-purple-50',
      borderColor: 'border-purple-200',
    },
    {
      key: 'addresses',
      label: 'Addresses',
      icon: MapPin,
      count: breakdown.addresses,
      items: detected_pii.addresses,
      color: 'text-orange-600',
      bgColor: 'bg-orange-50',
      borderColor: 'border-orange-200',
    },
  ];

  return (
    <div className="space-y-6">
      {/* Summary Card */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xl font-semibold text-gray-900">Detection Summary</h3>
          <div className="flex items-center space-x-2">
            {total_pii_found > 0 ? (
              <AlertTriangle className="w-5 h-5 text-warning-500" />
            ) : (
              <CheckCircle className="w-5 h-5 text-success-500" />
            )}
            <span className={`text-sm font-medium ${
              total_pii_found > 0 ? 'text-warning-600' : 'text-success-600'
            }`}>
              {total_pii_found > 0 ? 'PII Detected' : 'No PII Found'}
            </span>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <div className="text-3xl font-bold text-gray-900">{total_pii_found}</div>
            <div className="text-sm text-gray-600">Total PII Entities</div>
          </div>
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <div className="text-3xl font-bold text-gray-900">
              {confidence_score ? `${Math.round(confidence_score * 100)}%` : 'N/A'}
            </div>
            <div className="text-sm text-gray-600">Confidence Score</div>
          </div>
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <div className="flex items-center justify-center space-x-2">
              <Eye className="w-6 h-6 text-gray-600" />
              <span className="text-lg font-semibold text-gray-900">
                {contains_faces ? 'Yes' : 'No'}
              </span>
            </div>
            <div className="text-sm text-gray-600">Contains Faces</div>
          </div>
        </div>
      </div>

      {/* PII Types Breakdown */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {piiTypes.map((type) => (
          <div
            key={type.key}
            className={`bg-white rounded-xl border ${type.borderColor} p-6 ${
              type.count > 0 ? 'ring-2 ring-opacity-20' : ''
            }`}
          >
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-3">
                <div className={`p-2 rounded-lg ${type.bgColor}`}>
                  <type.icon className={`w-5 h-5 ${type.color}`} />
                </div>
                <div>
                  <h4 className="font-semibold text-gray-900">{type.label}</h4>
                  <p className="text-sm text-gray-600">
                    {type.count} {type.count === 1 ? 'item' : 'items'} found
                  </p>
                </div>
              </div>
              <div className={`text-2xl font-bold ${type.color}`}>
                {type.count}
              </div>
            </div>

            {type.count > 0 && (
              <div className="space-y-2">
                <div className="text-sm font-medium text-gray-700 mb-2">Detected Items:</div>
                <div className="max-h-32 overflow-y-auto space-y-1">
                  {type.items.slice(0, 10).map((item, index) => (
                    <div
                      key={index}
                      className="text-sm text-gray-600 bg-gray-50 px-3 py-2 rounded-lg truncate"
                      title={item}
                    >
                      {item}
                    </div>
                  ))}
                  {type.items.length > 10 && (
                    <div className="text-xs text-gray-500 text-center py-1">
                      ... and {type.items.length - 10} more
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Additional Info */}
      {detection.detection_summary.pii_class && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-start space-x-3">
            <div className="p-1 bg-blue-100 rounded">
              <AlertTriangle className="w-4 h-4 text-blue-600" />
            </div>
            <div>
              <h4 className="text-sm font-medium text-blue-800">PII Classification</h4>
              <p className="text-sm text-blue-700 mt-1">
                Document classified as: <strong>{detection.detection_summary.pii_class}</strong>
              </p>
              {detection.detection_summary.country_of_origin && (
                <p className="text-xs text-blue-600 mt-1">
                  Country of origin: {detection.detection_summary.country_of_origin}
                </p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PIIDisplay;
