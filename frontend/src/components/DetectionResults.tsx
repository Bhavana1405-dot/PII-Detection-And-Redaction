import React, { useState } from 'react';
import { DetectionResultsProps } from '../types';
import { 
  Mail, 
  Phone, 
  CreditCard, 
  MapPin, 
  Eye, 
  EyeOff, 
  Shield, 
  AlertTriangle,
  CheckCircle,
  Clock
} from 'lucide-react';

const DetectionResults: React.FC<DetectionResultsProps> = ({ result }) => {
  const [showDetails, setShowDetails] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);

  const { detection_summary, detected_pii } = result;
  const { total_pii_found, breakdown, pii_class, confidence_score, country_of_origin, contains_faces } = detection_summary;

  const getPIIIcon = (type: string) => {
    switch (type) {
      case 'emails':
        return <Mail className="w-5 h-5" />;
      case 'phone_numbers':
        return <Phone className="w-5 h-5" />;
      case 'identifiers':
        return <CreditCard className="w-5 h-5" />;
      case 'addresses':
        return <MapPin className="w-5 h-5" />;
      default:
        return <Shield className="w-5 h-5" />;
    }
  };

  const getPIIColor = (type: string) => {
    switch (type) {
      case 'emails':
        return 'text-blue-600 bg-blue-100';
      case 'phone_numbers':
        return 'text-green-600 bg-green-100';
      case 'identifiers':
        return 'text-purple-600 bg-purple-100';
      case 'addresses':
        return 'text-orange-600 bg-orange-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  const getConfidenceColor = (score: number) => {
    if (score >= 0.8) return 'text-success-600 bg-success-100';
    if (score >= 0.6) return 'text-warning-600 bg-warning-100';
    return 'text-danger-600 bg-danger-100';
  };

  const getRiskLevel = (total: number) => {
    if (total === 0) return { level: 'Low', color: 'text-success-600 bg-success-100' };
    if (total <= 5) return { level: 'Medium', color: 'text-warning-600 bg-warning-100' };
    return { level: 'High', color: 'text-danger-600 bg-danger-100' };
  };

  const riskLevel = getRiskLevel(total_pii_found);

  return (
    <div className="space-y-6">
      {/* Summary Card */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-900">Detection Summary</h2>
          <div className={`px-3 py-1 rounded-full text-sm font-medium ${riskLevel.color}`}>
            {riskLevel.level} Risk
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <div className="text-3xl font-bold text-gray-900">{total_pii_found}</div>
            <div className="text-sm text-gray-600">Total PII Found</div>
          </div>
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <div className="text-3xl font-bold text-gray-900">{Math.round(confidence_score * 100)}%</div>
            <div className="text-sm text-gray-600">Confidence Score</div>
          </div>
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <div className="text-3xl font-bold text-gray-900">{country_of_origin || 'Unknown'}</div>
            <div className="text-sm text-gray-600">Country of Origin</div>
          </div>
        </div>

        {/* PII Breakdown */}
        <div className="space-y-3">
          <h3 className="font-medium text-gray-900">PII Breakdown</h3>
          {Object.entries(breakdown).map(([type, count]) => (
            <div key={type} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center space-x-3">
                <div className={`p-2 rounded-lg ${getPIIColor(type)}`}>
                  {getPIIIcon(type)}
                </div>
                <span className="font-medium text-gray-900 capitalize">
                  {type.replace('_', ' ')}
                </span>
              </div>
              <div className="flex items-center space-x-2">
                <span className="text-2xl font-bold text-gray-900">{count}</span>
                <span className="text-sm text-gray-500">items</span>
              </div>
            </div>
          ))}
        </div>

        {/* Additional Info */}
        <div className="mt-6 pt-4 border-t border-gray-200">
          <div className="flex items-center justify-between text-sm">
            <div className="flex items-center space-x-2">
              <Clock className="w-4 h-4 text-gray-400" />
              <span className="text-gray-600">Scan completed at {new Date(result.timestamp).toLocaleTimeString()}</span>
            </div>
            <div className="flex items-center space-x-2">
              {contains_faces ? (
                <div className="flex items-center space-x-1 text-warning-600">
                  <Eye className="w-4 h-4" />
                  <span>Contains faces</span>
                </div>
              ) : (
                <div className="flex items-center space-x-1 text-success-600">
                  <EyeOff className="w-4 h-4" />
                  <span>No faces detected</span>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Detailed Results */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Detailed Results</h3>
          <button
            onClick={() => setShowDetails(!showDetails)}
            className="btn-secondary text-sm"
          >
            {showDetails ? 'Hide Details' : 'Show Details'}
          </button>
        </div>

        {showDetails && (
          <div className="space-y-4">
            {Object.entries(detected_pii).map(([category, items]) => (
              items.length > 0 && (
                <div key={category} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center space-x-2 mb-3">
                    <div className={`p-2 rounded-lg ${getPIIColor(category)}`}>
                      {getPIIIcon(category)}
                    </div>
                    <h4 className="font-medium text-gray-900 capitalize">
                      {category.replace('_', ' ')} ({items.length})
                    </h4>
                  </div>
                  
                  <div className="space-y-2">
                    {items.map((item, index) => (
                      <div key={index} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                        <div className="flex-1">
                          <div className="font-mono text-sm text-gray-900">
                            {item.value}
                          </div>
                          {item.confidence && (
                            <div className="text-xs text-gray-500 mt-1">
                              Confidence: {Math.round(item.confidence * 100)}%
                            </div>
                          )}
                        </div>
                        <div className="flex items-center space-x-2">
                          <div className={`px-2 py-1 rounded text-xs font-medium ${getConfidenceColor(item.confidence || 0)}`}>
                            {item.confidence ? Math.round(item.confidence * 100) : 'N/A'}%
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )
            ))}
          </div>
        )}
      </div>

      {/* Security Notice */}
      <div className="card border-warning-200 bg-warning-50">
        <div className="flex items-start space-x-3">
          <AlertTriangle className="w-5 h-5 text-warning-600 flex-shrink-0 mt-0.5" />
          <div>
            <h4 className="font-medium text-warning-800">Security Recommendation</h4>
            <p className="text-sm text-warning-700 mt-1">
              {total_pii_found > 0 
                ? `This document contains ${total_pii_found} PII entities. Consider redacting sensitive information before sharing.`
                : 'No PII detected in this document. It appears to be safe for sharing.'
              }
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DetectionResults;
