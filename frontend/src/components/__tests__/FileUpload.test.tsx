import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import FileUpload from '../FileUpload';

// Mock react-dropzone
jest.mock('react-dropzone', () => ({
  useDropzone: () => ({
    getRootProps: () => ({
      'data-testid': 'dropzone'
    }),
    getInputProps: () => ({
      'data-testid': 'file-input'
    }),
    isDragActive: false,
    fileRejections: []
  })
}));

describe('FileUpload', () => {
  const mockOnFileSelect = jest.fn();

  beforeEach(() => {
    mockOnFileSelect.mockClear();
  });

  it('renders upload interface', () => {
    render(<FileUpload onFileSelect={mockOnFileSelect} isProcessing={false} />);
    
    expect(screen.getByText('Upload Document')).toBeInTheDocument();
    expect(screen.getByText('Drag & drop a file here, or click to select')).toBeInTheDocument();
    expect(screen.getByText('Supports: PDF, Images (PNG, JPG, JPEG), Text files')).toBeInTheDocument();
  });

  it('shows processing state', () => {
    render(<FileUpload onFileSelect={mockOnFileSelect} isProcessing={true} />);
    
    expect(screen.getByText('Processing...')).toBeInTheDocument();
  });

  it('has correct dropzone attributes', () => {
    render(<FileUpload onFileSelect={mockOnFileSelect} isProcessing={false} />);
    
    expect(screen.getByTestId('dropzone')).toBeInTheDocument();
    expect(screen.getByTestId('file-input')).toBeInTheDocument();
  });
});
