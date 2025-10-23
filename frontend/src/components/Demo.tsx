import React from 'react';
import { Shield, Upload, Eye, Download } from 'lucide-react';

const Demo: React.FC = () => {
  return (
    <div className="bg-gradient-to-br from-primary-50 to-primary-100 rounded-2xl p-8 mb-8">
      <div className="text-center mb-8">
        <div className="inline-flex items-center justify-center w-16 h-16 bg-primary-600 rounded-full mb-4">
          <Shield className="w-8 h-8 text-white" />
        </div>
        <h2 className="text-3xl font-bold text-gray-900 mb-4">
          How It Works
        </h2>
        <p className="text-lg text-gray-600 max-w-2xl mx-auto">
          Our PII detection and redaction process is simple, secure, and efficient.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="text-center">
          <div className="inline-flex items-center justify-center w-12 h-12 bg-white rounded-full mb-4 shadow-sm">
            <Upload className="w-6 h-6 text-primary-600" />
          </div>
          <h3 className="font-semibold text-gray-900 mb-2">1. Upload</h3>
          <p className="text-sm text-gray-600">
            Upload your document using drag & drop or file picker
          </p>
        </div>

        <div className="text-center">
          <div className="inline-flex items-center justify-center w-12 h-12 bg-white rounded-full mb-4 shadow-sm">
            <Eye className="w-6 h-6 text-primary-600" />
          </div>
          <h3 className="font-semibold text-gray-900 mb-2">2. Detect</h3>
          <p className="text-sm text-gray-600">
            AI analyzes your document to identify PII entities
          </p>
        </div>

        <div className="text-center">
          <div className="inline-flex items-center justify-center w-12 h-12 bg-white rounded-full mb-4 shadow-sm">
            <Shield className="w-6 h-6 text-primary-600" />
          </div>
          <h3 className="font-semibold text-gray-900 mb-2">3. Redact</h3>
          <p className="text-sm text-gray-600">
            Choose your preferred redaction method and apply it
          </p>
        </div>

        <div className="text-center">
          <div className="inline-flex items-center justify-center w-12 h-12 bg-white rounded-full mb-4 shadow-sm">
            <Download className="w-6 h-6 text-primary-600" />
          </div>
          <h3 className="font-semibold text-gray-900 mb-2">4. Download</h3>
          <p className="text-sm text-gray-600">
            Download your redacted document and detailed report
          </p>
        </div>
      </div>
    </div>
  );
};

export default Demo;
