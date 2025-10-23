import React, { useState, useCallback } from 'react';
import Header from './components/Header';
import Footer from './components/Footer';
import FileUpload from './components/FileUpload';
import PIIDisplay from './components/PIIDisplay';
import RedactionControls from './components/RedactionControls';
import Demo from './components/Demo';
import { DetectionResponse, RedactionResponse } from './types';
import apiService from './services/api';

function App() {
  const [currentFile, setCurrentFile] = useState<File | null>(null);
  const [detection, setDetection] = useState<DetectionResponse | null>(null);
  const [redactionResult, setRedactionResult] = useState<RedactionResponse | null>(null);
  const [isDetecting, setIsDetecting] = useState(false);
  const [isRedacting, setIsRedacting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFileSelect = useCallback(async (file: File) => {
    setCurrentFile(file);
    setDetection(null);
    setRedactionResult(null);
    setError(null);
    setIsDetecting(true);

    try {
      const result = await apiService.detectPII(file);
      setDetection(result);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Detection failed');
    } finally {
      setIsDetecting(false);
    }
  }, []);

  const handleRedact = useCallback(async (method: string) => {
    if (!currentFile || !detection) return;

    setIsRedacting(true);
    setError(null);

    try {
      const result = await apiService.redactPII(
        currentFile, 
        detection.report_file, 
        method
      );
      setRedactionResult(result);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Redaction failed');
    } finally {
      setIsRedacting(false);
    }
  }, [currentFile, detection]);

  const handleNewFile = useCallback(() => {
    setCurrentFile(null);
    setDetection(null);
    setRedactionResult(null);
    setError(null);
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <Header />
      
      <main className="flex-1">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {/* Hero Section */}
          <div className="text-center mb-12">
            <h1 className="text-4xl font-bold text-gray-900 mb-4">
              PII Detection & Redaction
            </h1>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Automatically detect and redact personally identifiable information from your documents 
              with advanced AI technology. Protect privacy while maintaining document integrity.
            </p>
          </div>

          {/* Demo Section */}
          <Demo />

          {/* Upload Section */}
          <section id="upload" className="mb-12">
            <div className="max-w-4xl mx-auto">
              <h2 className="text-2xl font-semibold text-gray-900 mb-6 text-center">
                Upload Document
              </h2>
              <FileUpload
                onFileSelect={handleFileSelect}
                isProcessing={isDetecting}
              />
              
              {currentFile && (
                <div className="mt-6 p-4 bg-white rounded-lg border border-gray-200">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div className="p-2 bg-primary-100 rounded-lg">
                        <svg className="w-5 h-5 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                      </div>
                      <div>
                        <p className="font-medium text-gray-900">{currentFile.name}</p>
                        <p className="text-sm text-gray-500">
                          {(currentFile.size / 1024 / 1024).toFixed(2)} MB
                        </p>
                      </div>
                    </div>
                    <button
                      onClick={handleNewFile}
                      className="text-sm text-gray-500 hover:text-gray-700"
                    >
                      Upload New File
                    </button>
                  </div>
                </div>
              )}
            </div>
          </section>

          {/* Detection Results */}
          {currentFile && (
            <section id="detect" className="mb-12">
              <div className="max-w-6xl mx-auto">
                <h2 className="text-2xl font-semibold text-gray-900 mb-6 text-center">
                  PII Detection Results
                </h2>
                <PIIDisplay
                  detection={detection}
                  isLoading={isDetecting}
                  error={error}
                />
              </div>
            </section>
          )}

          {/* Redaction Controls */}
          {detection && (
            <section id="redact" className="mb-12">
              <div className="max-w-6xl mx-auto">
                <h2 className="text-2xl font-semibold text-gray-900 mb-6 text-center">
                  Redaction Controls
                </h2>
                <RedactionControls
                  detection={detection}
                  onRedact={handleRedact}
                  isRedacting={isRedacting}
                  redactionResult={redactionResult}
                />
              </div>
            </section>
          )}


          {/* Features Section */}
          <section className="py-16 bg-white rounded-2xl shadow-sm">
            <div className="max-w-6xl mx-auto px-6">
              <h2 className="text-3xl font-bold text-gray-900 text-center mb-12">
                Why Choose PII Redactor?
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                <div className="text-center">
                  <div className="p-4 bg-primary-100 rounded-full w-16 h-16 mx-auto mb-4 flex items-center justify-center">
                    <svg className="w-8 h-8 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <h3 className="text-xl font-semibold text-gray-900 mb-2">Accurate Detection</h3>
                  <p className="text-gray-600">
                    Advanced AI models detect PII with high accuracy across multiple document types.
                  </p>
                </div>
                <div className="text-center">
                  <div className="p-4 bg-success-100 rounded-full w-16 h-16 mx-auto mb-4 flex items-center justify-center">
                    <svg className="w-8 h-8 text-success-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                    </svg>
                  </div>
                  <h3 className="text-xl font-semibold text-gray-900 mb-2">Secure Processing</h3>
                  <p className="text-gray-600">
                    Your documents are processed securely with no data retention or logging.
                  </p>
                </div>
                <div className="text-center">
                  <div className="p-4 bg-warning-100 rounded-full w-16 h-16 mx-auto mb-4 flex items-center justify-center">
                    <svg className="w-8 h-8 text-warning-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                  </div>
                  <h3 className="text-xl font-semibold text-gray-900 mb-2">Fast Processing</h3>
                  <p className="text-gray-600">
                    Quick processing times with support for batch operations and large files.
                  </p>
                </div>
              </div>
            </div>
          </section>
        </div>
      </main>

      <Footer />
    </div>
  );
}

export default App;
