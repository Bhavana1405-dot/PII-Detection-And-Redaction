import React, { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, File, AlertCircle, Loader2 } from 'lucide-react';
import { FileUploadProps } from '../types';

const FileUpload: React.FC<FileUploadProps> = ({ 
  onFileSelect, 
  isProcessing, 
  acceptedTypes = ".pdf,.png,.jpg,.jpeg,.txt,.csv,.md" 
}) => {
  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      onFileSelect(acceptedFiles[0]);
    }
  }, [onFileSelect]);

  const { getRootProps, getInputProps, isDragActive, fileRejections } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'image/*': ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff'],
      'text/plain': ['.txt'],
      'text/csv': ['.csv'],
      'text/markdown': ['.md'],
    },
    multiple: false,
    disabled: isProcessing,
  });

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="w-full">
      <div
        {...getRootProps()}
        className={`
          relative border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all duration-200
          ${isDragActive 
            ? 'border-primary-500 bg-primary-50' 
            : 'border-gray-300 hover:border-primary-400 hover:bg-gray-50'
          }
          ${isProcessing ? 'opacity-50 cursor-not-allowed' : ''}
        `}
      >
        <input {...getInputProps()} />
        
        <div className="flex flex-col items-center space-y-4">
          {isProcessing ? (
            <Loader2 className="w-12 h-12 text-primary-500 animate-spin" />
          ) : (
            <div className="p-4 bg-primary-100 rounded-full">
              <Upload className="w-8 h-8 text-primary-600" />
            </div>
          )}
          
          <div className="space-y-2">
            <h3 className="text-lg font-semibold text-gray-900">
              {isProcessing ? 'Processing...' : 'Upload Document'}
            </h3>
            <p className="text-gray-600">
              {isDragActive 
                ? 'Drop your file here' 
                : 'Drag & drop a file here, or click to select'
              }
            </p>
            <p className="text-sm text-gray-500">
              Supports: PDF, Images (PNG, JPG, JPEG), Text files
            </p>
            <p className="text-xs text-gray-400">
              Max file size: 10MB
            </p>
          </div>
        </div>

        {isProcessing && (
          <div className="absolute inset-0 bg-white bg-opacity-75 flex items-center justify-center rounded-xl">
            <div className="text-center">
              <Loader2 className="w-8 h-8 text-primary-500 animate-spin mx-auto mb-2" />
              <p className="text-sm text-gray-600">Analyzing document...</p>
            </div>
          </div>
        )}
      </div>

      {fileRejections.length > 0 && (
        <div className="mt-4 p-4 bg-danger-50 border border-danger-200 rounded-lg">
          <div className="flex items-start space-x-2">
            <AlertCircle className="w-5 h-5 text-danger-500 mt-0.5 flex-shrink-0" />
            <div>
              <h4 className="text-sm font-medium text-danger-800">File rejected</h4>
              <ul className="mt-1 text-sm text-danger-700">
                {fileRejections.map(({ file, errors }) => (
                  <li key={file.name}>
                    <strong>{file.name}</strong> ({formatFileSize(file.size)})
                    <ul className="ml-4 mt-1">
                      {errors.map((error) => (
                        <li key={error.code}>• {error.message}</li>
                      ))}
                    </ul>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default FileUpload;
