import React from 'react';
import { Shield, Github, Mail, ExternalLink } from 'lucide-react';

const Footer: React.FC = () => {
  return (
    <footer className="bg-gray-50 border-t border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          {/* Brand */}
          <div className="col-span-1 md:col-span-2">
            <div className="flex items-center space-x-3 mb-4">
              <div className="p-2 bg-primary-600 rounded-lg">
                <Shield className="w-5 h-5 text-white" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-gray-900">PII Redactor</h3>
                <p className="text-sm text-gray-600">Advanced Privacy Protection</p>
              </div>
            </div>
            <p className="text-sm text-gray-600 max-w-md">
              Automatically detect and redact personally identifiable information from documents 
              with state-of-the-art AI technology. Protect privacy while maintaining document integrity.
            </p>
          </div>

          {/* Features */}
          <div>
            <h4 className="text-sm font-semibold text-gray-900 mb-4">Features</h4>
            <ul className="space-y-2 text-sm text-gray-600">
              <li>• PII Detection</li>
              <li>• Multiple Redaction Methods</li>
              <li>• PDF & Image Support</li>
              <li>• Batch Processing</li>
              <li>• Audit Logging</li>
            </ul>
          </div>

          {/* Support */}
          <div>
            <h4 className="text-sm font-semibold text-gray-900 mb-4">Support</h4>
            <ul className="space-y-2 text-sm text-gray-600">
              <li>
                <a 
                  href="https://github.com" 
                  className="flex items-center space-x-2 hover:text-primary-600 transition-colors"
                >
                  <Github className="w-4 h-4" />
                  <span>GitHub</span>
                  <ExternalLink className="w-3 h-3" />
                </a>
              </li>
              <li>
                <a 
                  href="mailto:support@example.com" 
                  className="flex items-center space-x-2 hover:text-primary-600 transition-colors"
                >
                  <Mail className="w-4 h-4" />
                  <span>Contact</span>
                </a>
              </li>
            </ul>
          </div>
        </div>

        <div className="mt-8 pt-8 border-t border-gray-200">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <p className="text-sm text-gray-500">
              © 2024 PII Redactor. All rights reserved.
            </p>
            <div className="flex space-x-6 mt-4 md:mt-0">
              <button className="text-sm text-gray-500 hover:text-gray-700">
                Privacy Policy
              </button>
              <button className="text-sm text-gray-500 hover:text-gray-700">
                Terms of Service
              </button>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
