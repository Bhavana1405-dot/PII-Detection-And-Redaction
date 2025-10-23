import React from 'react';
import { Shield, Github, Settings } from 'lucide-react';

const Header: React.FC = () => {
  return (
    <header className="bg-white border-b border-gray-200 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo and Title */}
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-primary-600 rounded-lg">
              <Shield className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-900">PII Redactor</h1>
              <p className="text-xs text-gray-500">Privacy Protection Tool</p>
            </div>
          </div>

          {/* Navigation */}
          <nav className="hidden md:flex items-center space-x-6">
            <a
              href="#upload"
              className="text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors"
            >
              Upload
            </a>
            <a
              href="#detect"
              className="text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors"
            >
              Detect
            </a>
            <a
              href="#redact"
              className="text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors"
            >
              Redact
            </a>
          </nav>

          {/* Actions */}
          <div className="flex items-center space-x-3">
            <button className="p-2 text-gray-400 hover:text-gray-600 transition-colors">
              <Settings className="w-5 h-5" />
            </button>
            <a
              href="https://github.com"
              target="_blank"
              rel="noopener noreferrer"
              className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
            >
              <Github className="w-5 h-5" />
            </a>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
