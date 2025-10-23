# PII Shield Frontend

A modern, responsive React application for PII (Personally Identifiable Information) detection and redaction. Built with React, TypeScript, Tailwind CSS, and Vite.

## Features

- 🎯 **Drag & Drop Upload**: Easy file upload with support for PDF and image files
- 🔍 **AI-Powered Detection**: Advanced PII detection using Octopii engine
- 🛡️ **Multiple Redaction Methods**: Blur, black box, and pixelation options
- 📱 **Responsive Design**: Works seamlessly on desktop, tablet, and mobile
- 🎨 **Modern UI**: Clean, minimalist interface with smooth animations
- 📊 **Detailed Analytics**: Comprehensive PII detection reports and statistics
- 🔒 **Privacy-First**: Local processing with secure data handling

## Tech Stack

- **React 19** - Modern React with hooks and functional components
- **TypeScript** - Type-safe development
- **Tailwind CSS** - Utility-first CSS framework
- **Lucide React** - Beautiful, customizable icons
- **React Dropzone** - Drag and drop file uploads
- **Axios** - HTTP client for API communication

## Getting Started

### Prerequisites

- Node.js 16+ 
- npm or yarn
- Backend API running on port 8000

### Installation

1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm start
```

3. Open [http://localhost:3000](http://localhost:3000) in your browser

### Building for Production

```bash
npm run build
```

The build artifacts will be stored in the `build/` directory.

## Project Structure

```
src/
├── components/          # React components
│   ├── Header.tsx      # Application header
│   ├── FileUpload.tsx  # File upload with drag & drop
│   ├── DetectionResults.tsx  # PII detection results display
│   ├── RedactionControls.tsx # Redaction method selection
│   └── LoadingSpinner.tsx    # Loading states
├── types.ts            # TypeScript type definitions
├── App.tsx             # Main application component
└── index.css           # Global styles and Tailwind imports
```

## API Integration

The frontend communicates with the backend API at `http://localhost:8000`:

- `POST /detect-pii/` - Upload file for PII detection
- `POST /redact-pii/` - Redact PII from uploaded file
- `GET /download-redacted/{filename}` - Download redacted file
- `GET /download-report/{filename}` - Download detection report

## Supported File Types

- **PDF**: `.pdf`
- **Images**: `.png`, `.jpg`, `.jpeg`, `.gif`, `.bmp`, `.tiff`
- **Max Size**: 50MB

## PII Detection Types

- **Emails**: Email addresses
- **Phone Numbers**: Phone and mobile numbers
- **Identifiers**: SSN, Aadhaar, PAN, Driver's License, etc.
- **Addresses**: Physical addresses and locations
- **Faces**: Human faces in images

## Redaction Methods

1. **Blur**: Apply Gaussian blur to sensitive areas
2. **Black Box**: Cover with solid black rectangles
3. **Pixelate**: Apply pixelation effect to sensitive areas

## Responsive Design

The application is fully responsive with breakpoints:
- **Mobile**: < 640px
- **Tablet**: 640px - 1024px
- **Desktop**: > 1024px
- **Large Desktop**: > 1280px

## Customization

### Colors
The color scheme can be customized in `tailwind.config.js`:

```javascript
theme: {
  extend: {
    colors: {
      primary: { /* Primary color palette */ },
      danger: { /* Error/danger colors */ },
      success: { /* Success colors */ },
      warning: { /* Warning colors */ }
    }
  }
}
```

### Components
All components are modular and can be easily customized or extended.

## Security Features

- Client-side file validation
- Secure API communication
- No permanent file storage
- Privacy-focused design
- Local processing capabilities

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Development

### Available Scripts

- `npm start` - Start development server
- `npm run build` - Build for production
- `npm test` - Run tests
- `npm run eject` - Eject from Create React App

### Code Style

- ESLint configuration included
- Prettier recommended
- TypeScript strict mode enabled
- Tailwind CSS utility classes

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is part of the PII Redaction system. See the main project for license information.