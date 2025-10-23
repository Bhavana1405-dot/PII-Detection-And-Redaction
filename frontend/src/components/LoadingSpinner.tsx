import React from 'react';

const LoadingSpinner: React.FC = () => {
  return (
    <div className="card text-center py-12">
      <div className="mx-auto w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center mb-4">
        <div className="animate-spin rounded-full h-8 w-8 border-4 border-primary-600 border-t-transparent"></div>
      </div>
      <h3 className="text-lg font-medium text-gray-900 mb-2">Processing Document</h3>
      <p className="text-gray-500">Please wait while we analyze your document for PII information...</p>
      
      <div className="mt-6 space-y-2">
        <div className="flex items-center justify-center space-x-2 text-sm text-gray-600">
          <div className="w-2 h-2 bg-primary-600 rounded-full animate-pulse"></div>
          <span>Scanning document</span>
        </div>
        <div className="flex items-center justify-center space-x-2 text-sm text-gray-600">
          <div className="w-2 h-2 bg-primary-600 rounded-full animate-pulse" style={{ animationDelay: '0.2s' }}></div>
          <span>Detecting PII entities</span>
        </div>
        <div className="flex items-center justify-center space-x-2 text-sm text-gray-600">
          <div className="w-2 h-2 bg-primary-600 rounded-full animate-pulse" style={{ animationDelay: '0.4s' }}></div>
          <span>Generating report</span>
        </div>
      </div>
    </div>
  );
};

export default LoadingSpinner;
