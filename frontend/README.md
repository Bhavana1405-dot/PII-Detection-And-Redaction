# PII Redactor Frontend

A modern, sleek React TypeScript frontend for the PII Detection and Redaction application.

## Features

- **Modern UI/UX**: Clean, minimalist design with Tailwind CSS
- **Drag & Drop Upload**: Easy file upload with visual feedback
- **Real-time PII Detection**: Live analysis and visualization of detected PII
- **Multiple Redaction Methods**: Blur, black box, and pixelate options
- **Responsive Design**: Works seamlessly on desktop and mobile devices
- **TypeScript**: Full type safety and better development experience

## Tech Stack

- **React 19** with TypeScript
- **Tailwind CSS** for styling
- **Axios** for API communication
- **React Dropzone** for file uploads
- **Lucide React** for icons

## Getting Started

### Prerequisites

- Node.js 16+ 
- npm or yarn
- Backend API running on http://localhost:8000

### Installation

1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm start
```

3. Open [http://localhost:3000](http://localhost:3000) to view it in the browser.

### Building for Production

```bash
npm run build
```

This builds the app for production to the `build` folder.

## Project Structure

```
src/
├── components/          # React components
│   ├── FileUpload.tsx   # File upload with drag & drop
│   ├── PIIDisplay.tsx   # PII detection results display
│   ├── RedactionControls.tsx # Redaction method selection
│   ├── Header.tsx       # Application header
│   └── Footer.tsx       # Application footer
├── services/            # API services
│   └── api.ts          # Backend API integration
├── types/              # TypeScript type definitions
│   └── index.ts        # Shared types
├── App.tsx             # Main application component
└── index.css           # Global styles with Tailwind
```

## API Integration

The frontend communicates with the backend API through the following endpoints:

- `POST /detect-pii/` - Upload file for PII detection
- `POST /redact-pii/` - Redact PII from uploaded file
- `GET /download-redacted/{filename}` - Download redacted file
- `GET /download-report/{filename}` - Download detection report

## Styling

The application uses Tailwind CSS with a custom color palette:

- **Primary**: Blue tones for main actions and branding
- **Success**: Green tones for success states
- **Warning**: Orange/yellow tones for warnings
- **Danger**: Red tones for errors and alerts

## Development

### Available Scripts

- `npm start` - Runs the app in development mode
- `npm test` - Launches the test runner
- `npm run build` - Builds the app for production
- `npm run eject` - Ejects from Create React App (one-way operation)

### Code Style

- Use TypeScript for all components
- Follow React functional component patterns with hooks
- Use Tailwind CSS classes for styling
- Implement proper error handling and loading states
- Use semantic HTML elements for accessibility

## Contributing

1. Follow the existing code style and patterns
2. Add proper TypeScript types for new features
3. Test components thoroughly
4. Ensure responsive design works on all screen sizes