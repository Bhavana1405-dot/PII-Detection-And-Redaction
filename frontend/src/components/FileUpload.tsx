import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { FileUploadProps } from '../types';
import { Upload, File, X, AlertCircle } from 'lucide-react';
import { piiApi } from '../services/api';

const FileUpload: React.FC<FileUploadProps> = ({ onDetectionComplete, onError, onLoading }) => {
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const file = acceptedFiles[0];
    if (file) {
      setUploadedFile(file);
      handleFileUpload(file);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'image/*': ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff']
    },
    maxFiles: 1,
    maxSize: 50 * 1024 * 1024 // 50MB
  });

  const handleFileUpload = async (file: File) => {
    setIsUploading(true);
    onLoading(true);

    try {
      const result = await piiApi.detectPII(file);
      // pass both the detection result and the original File so the app
      // can reuse the same File for redaction without re-selecting
      onDetectionComplete(result, file);
    } catch (error) {
      console.error('Upload error:', error);
      onError(error instanceof Error ? error.message : 'An error occurred during detection');
    } finally {
      setIsUploading(false);
      onLoading(false);
    }
  };

  const removeFile = () => {
    setUploadedFile(null);
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getFileIcon = (file: File) => {
    if (file.type === 'application/pdf') {
      return <File className="w-8 h-8 text-red-500" />;
    }
    return <File className="w-8 h-8 text-blue-500" />;
  };

  return (
    <div className="card">
      <div className="mb-4">
        <h2 className="text-lg font-semibold text-gray-900 mb-2">Upload Document</h2>
        <p className="text-sm text-gray-600">Upload a PDF or image file to detect PII information</p>
      </div>

      {!uploadedFile ? (
        <div
          {...getRootProps()}
          className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
            isDragActive
              ? 'border-primary-400 bg-primary-50'
              : 'border-gray-300 hover:border-primary-400 hover:bg-gray-50'
          }`}
        >
          <input {...getInputProps()} />
          <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          {isDragActive ? (
            <p className="text-primary-600 font-medium">Drop the file here...</p>
          ) : (
            <div>
              <p className="text-gray-600 font-medium mb-2">
                Drag & drop a file here, or click to select
              </p>
              <p className="text-sm text-gray-500">
                Supports PDF, PNG, JPG, JPEG, GIF, BMP, TIFF (max 50MB)
              </p>
            </div>
          )}
        </div>
      ) : (
        <div className="border border-gray-200 rounded-lg p-4 bg-gray-50">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              {getFileIcon(uploadedFile)}
              <div>
                <p className="font-medium text-gray-900">{uploadedFile.name}</p>
                <p className="text-sm text-gray-500">{formatFileSize(uploadedFile.size)}</p>
              </div>
            </div>
            <button
              onClick={removeFile}
              className="text-gray-400 hover:text-gray-600 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
          
          {isUploading && (
            <div className="mt-4 flex items-center space-x-2 text-sm text-primary-600">
              <div className="animate-spin rounded-full h-4 w-4 border-2 border-primary-600 border-t-transparent"></div>
              <span>Analyzing document...</span>
            </div>
          )}
        </div>
      )}

      <div className="mt-4 p-3 bg-blue-50 rounded-lg">
        <div className="flex items-start space-x-2">
          <AlertCircle className="w-5 h-5 text-blue-500 flex-shrink-0 mt-0.5" />
          <div className="text-sm text-blue-700">
            <p className="font-medium">Privacy Notice</p>
            <p>Your files are processed locally and securely. No data is stored permanently on our servers.</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FileUpload;
