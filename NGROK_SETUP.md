# 🌍 Ngrok Setup for AI PDF Analyzer

This guide shows you how to share your AI PDF Analyzer app publicly while keeping the backend secure and private.

## 🏗️ Architecture

```
Internet User → Ngrok (Public) → Frontend (Port 3000) → Next.js API Proxy → Backend (Port 8000, Private)
```

- ✅ **Frontend**: Publicly accessible via ngrok
- 🔒 **Backend**: Private, only accessible from your machine
- 🔄 **Proxy**: Next.js API routes forward requests to backend

## 🚀 Quick Start

### Option 1: Automated Script (Recommended)

```bash
# Make sure you have ngrok installed
brew install ngrok  # or download from https://ngrok.com/

# Run the setup script
./start-ngrok.sh
```

This script will:
1. Start the backend server (port 8000)
2. Start the frontend server (port 3000) 
3. Expose the frontend via ngrok
4. Show you the public URL

### Option 2: Manual Setup

1. **Start Backend** (Terminal 1):
```bash
cd backend
source bin/activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

2. **Start Frontend** (Terminal 2):
```bash
npm run dev
```

3. **Start Ngrok** (Terminal 3):
```bash
ngrok http 3000
```

## 🔧 How It Works

### Next.js Built-in Proxy

The frontend uses Next.js built-in proxy configuration:

```
Frontend Request: /api/documents/list
                      ↓
Next.js Config: rewrites in next.config.ts
                      ↓
Backend Request: http://localhost:8000/api/documents/list
```

### How It Works

- Frontend makes requests to `/api/*` (same as before)
- Next.js config automatically proxies these to `http://localhost:8000/api/*`
- No additional API routes needed - just configuration!
- Backend stays private on localhost:8000

## 📱 Sharing Your App

1. Run the setup script or manual setup
2. Copy the ngrok URL (e.g., `https://abc123.ngrok.io`)
3. Share this URL with others
4. They can access your app without knowing about the backend

## 🔒 Security Benefits

- ✅ Backend stays private (localhost:8000)
- ✅ Only frontend is exposed publicly
- ✅ All API calls go through your proxy
- ✅ You control what gets exposed
- ✅ Backend can't be accessed directly from internet

## 🛠️ Troubleshooting

### Backend Connection Issues
```bash
# Check if backend is running
curl http://localhost:8000/api/health

# Should return: {"status": "healthy", "version": "1.0.0"}
```

### Frontend Proxy Issues
```bash
# Check if Next.js proxy is working
curl http://localhost:3000/api/health

# Should return: {"status":"healthy","version":"1.0.0"}
```

### Ngrok Issues
- Visit http://localhost:4040 to see ngrok dashboard
- Check if ngrok is properly authenticated
- Ensure port 3000 is accessible

## 🔄 Development Workflow

1. **Local Development**: Use `npm run dev` and backend directly
2. **Sharing**: Use the ngrok setup script
3. **Testing**: Test with the ngrok URL before sharing

## 📝 Notes

- The backend must be running for the proxy to work
- Next.js config handles all proxying automatically
- No additional code needed - just configuration
- Works with all request types (GET, POST, file uploads, etc.)
- Backend stays completely private

## 🆘 Support

If you encounter issues:
1. Check that both backend and frontend are running
2. Verify ngrok is working at http://localhost:4040
3. Check browser console for API errors
4. Ensure all services are using the correct ports
