# Getting Started with PII Shield Frontend

## Quick Start

1. **Install Dependencies**
   ```bash
   cd frontend
   npm install
   ```

2. **Start the Backend API**
   ```bash
   # In the project root directory
   cd backend
   python main.py
   ```
   The API will run on `http://localhost:8000`

3. **Start the Frontend**
   ```bash
   # In the frontend directory
   npm start
   ```
   The app will open at `http://localhost:3000`

## Features Overview

### 🎯 File Upload
- Drag & drop interface for easy file upload
- Support for PDF and image files (PNG, JPG, JPEG, GIF, BMP, TIFF)
- File size validation (max 50MB)
- Real-time upload progress

### 🔍 PII Detection
- AI-powered detection of various PII types:
  - Email addresses
  - Phone numbers
  - Government IDs (SSN, Aadhaar, PAN, etc.)
  - Physical addresses
  - Human faces
- Confidence scoring for each detection
- Detailed breakdown by PII category

### 🛡️ Redaction Options
- **Blur**: Apply Gaussian blur to sensitive areas
- **Black Box**: Cover with solid black rectangles
- **Pixelate**: Apply pixelation effect
- Real-time preview of redaction methods

### 📊 Analytics & Reporting
- Comprehensive detection summary
- Risk level assessment (Low/Medium/High)
- Downloadable detection reports (JSON)
- Downloadable redacted files

### 📱 Responsive Design
- Mobile-first approach
- Optimized for all screen sizes
- Touch-friendly interface
- Progressive enhancement

## Architecture

### Component Structure
```
App.tsx
├── Header.tsx              # Navigation and branding
├── FileUpload.tsx          # File upload with drag & drop
├── DetectionResults.tsx    # PII detection results display
├── RedactionControls.tsx   # Redaction method selection
└── LoadingSpinner.tsx      # Loading states
```

### API Integration
- Centralized API service (`services/api.ts`)
- Axios-based HTTP client
- Error handling and timeout management
- Type-safe API responses

### Styling
- Tailwind CSS for utility-first styling
- Custom component classes
- Responsive design system
- Dark/light mode ready

## Customization

### Colors
Edit `tailwind.config.js` to customize the color scheme:
```javascript
colors: {
  primary: { /* Your primary colors */ },
  danger: { /* Error colors */ },
  success: { /* Success colors */ },
  warning: { /* Warning colors */ }
}
```

### Components
All components are modular and can be easily customized:
- Props-based configuration
- TypeScript interfaces for type safety
- Reusable design patterns

## Development

### Available Scripts
- `npm start` - Development server
- `npm run build` - Production build
- `npm test` - Run tests
- `npm run eject` - Eject from Create React App

### Code Quality
- ESLint configuration
- TypeScript strict mode
- Prettier formatting (recommended)
- Component documentation

## Troubleshooting

### Common Issues

1. **API Connection Failed**
   - Ensure backend is running on port 8000
   - Check CORS settings in backend
   - Verify API endpoints are accessible

2. **File Upload Issues**
   - Check file size (max 50MB)
   - Verify file type is supported
   - Ensure stable internet connection

3. **Build Issues**
   - Clear node_modules and reinstall
   - Check Node.js version (16+)
   - Verify all dependencies are installed

### Debug Mode
Enable debug logging by opening browser console. All API calls and errors are logged for debugging.

## Production Deployment

1. **Build the Application**
   ```bash
   npm run build
   ```

2. **Serve Static Files**
   - Use any static file server (nginx, Apache, etc.)
   - Or deploy to platforms like Vercel, Netlify, etc.

3. **Environment Variables**
   - Set `REACT_APP_API_URL` for production API endpoint
   - Configure CORS settings in backend

## Security Considerations

- Client-side file validation
- No permanent file storage
- Secure API communication
- Privacy-focused design
- Local processing capabilities

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Performance

- Lazy loading of components
- Optimized bundle size
- Efficient re-rendering
- Image optimization
- Code splitting ready

## Contributing

1. Follow the existing code style
2. Add TypeScript types for new features
3. Test on multiple screen sizes
4. Ensure accessibility compliance
5. Update documentation as needed
