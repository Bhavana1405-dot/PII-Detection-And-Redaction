import React, { useState } from 'react';
import Header from './components/Header';
import FileUpload from './components/FileUpload';
import DetectionResults from './components/DetectionResults';
import RedactionControls from './components/RedactionControls';
import LoadingSpinner from './components/LoadingSpinner';
import { PIIDetectionResult, RedactionMethod } from './types';

function App() {
  const [detectionResult, setDetectionResult] = useState<PIIDetectionResult | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [redactionMethod, setRedactionMethod] = useState<RedactionMethod>('blur');

  const handleDetectionComplete = (result: PIIDetectionResult, file: File) => {
    setDetectionResult(result);
    setSelectedFile(file);
    setError(null);
  };

  const handleError = (errorMessage: string) => {
    setError(errorMessage);
    setDetectionResult(null);
  };

  const handleLoading = (loading: boolean) => {
    setIsLoading(loading);
  };

  const handleRedactionComplete = (result: any) => {
    // Handle redaction completion
    console.log('Redaction completed:', result);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      
      <main className="container mx-auto px-4 py-4 sm:py-8 max-w-7xl">
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-4 sm:gap-6 lg:gap-8">
          {/* Left Column - Upload and Controls */}
          <div className="lg:col-span-1 space-y-6">
            <FileUpload
              onDetectionComplete={handleDetectionComplete}
              onError={handleError}
              onLoading={handleLoading}
            />
            
            {detectionResult && (
              <RedactionControls
                detectionResult={detectionResult}
                selectedFile={selectedFile || undefined}
                redactionMethod={redactionMethod}
                onMethodChange={setRedactionMethod}
                onRedactionComplete={handleRedactionComplete}
                onLoading={handleLoading}
              />
            )}
          </div>

          {/* Right Column - Results */}
          <div className="xl:col-span-2">
            {isLoading && <LoadingSpinner />}
            
            {error && (
              <div className="card border-danger-200 bg-danger-50">
                <div className="flex items-center space-x-3">
                  <div className="flex-shrink-0">
                    <svg className="h-5 w-5 text-danger-400" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <div>
                    <h3 className="text-sm font-medium text-danger-800">Error</h3>
                    <p className="text-sm text-danger-700 mt-1">{error}</p>
                  </div>
                </div>
              </div>
            )}

            {detectionResult && !isLoading && (
              <DetectionResults result={detectionResult} />
            )}

            {!detectionResult && !isLoading && !error && (
              <div className="card text-center py-12">
                <div className="mx-auto w-24 h-24 bg-gray-100 rounded-full flex items-center justify-center mb-4">
                  <svg className="w-12 h-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">Upload a Document</h3>
                <p className="text-gray-500">Upload a PDF or image file to detect and redact PII information</p>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;