# Google Cloud Vertex AI Video Generation Server

This Node.js/Express server uses Google Cloud Vertex AI (Veo) to generate videos from uploaded images.

## Setup Instructions

### 1. Environment Configuration

Create a `.env` file in the server directory with the following variables:

```env
GOOGLE_PROJECT_ID=hashitup-473320
GOOGLE_CLOUD_LOCATION=us-central1
VEO_MODEL=veo-1.0
GOOGLE_APPLICATION_CREDENTIALS=./service-account.json
FRONTEND_URL=http://localhost:3000
PORT=5000
```

### 2. Service Account Setup

1. Place your `service-account.json` file in the server directory
2. Ensure the service account has the following permissions:
   - `Vertex AI User` role
   - `AI Platform Developer` role
   - Or custom role with `aiplatform.endpoints.predict` permission

### 3. Install Dependencies

```bash
npm install
```

### 4. Start the Server

```bash
npm start
```

## API Endpoints

### Health Check
- **GET** `/api/health` - Check server status and authentication

### Authentication Test
- **GET** `/api/test-auth` - Test Google Cloud authentication

### Available Models
- **GET** `/api/models` - List available Vertex AI models

### Video Generation
- **POST** `/api/generate-video` - Generate video from uploaded image
  - **Body**: `multipart/form-data` with `image` field
  - **Response**: JSON with `videoUrl` and metadata

## Example Usage

```javascript
// Upload image and generate video
const formData = new FormData();
formData.append('image', imageFile);

const response = await fetch('/api/generate-video', {
  method: 'POST',
  body: formData
});

const result = await response.json();
console.log('Video URL:', result.videoUrl);
```

## Error Handling

The server includes comprehensive error handling:
- File cleanup on errors
- Detailed error logging
- Proper HTTP status codes
- Authentication error handling

## Debugging

Check the server console for detailed logs:
- ✅ Success indicators
- ❌ Error indicators
- 🔐 Authentication status
- 📁 File operations
- 🚀 API requests
- 🎬 Video generation status
