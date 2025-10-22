// Simple fetch-based API client
// Prefer direct calls to backend origin in production to avoid proxy issues
const backendOrigin = (() => {
  if (process.env.NEXT_PUBLIC_BACKEND_URL) return process.env.NEXT_PUBLIC_BACKEND_URL;
  if (process.env.NEXT_PUBLIC_BACKEND_HOST) return `https://${process.env.NEXT_PUBLIC_BACKEND_HOST}`;
  return '';
})();
const API_BASE_URL = backendOrigin ? `${backendOrigin}/api` : '/api';

// Helper function for API calls
async function apiCall(endpoint: string, options: RequestInit = {}) {
  const url = `${API_BASE_URL}${endpoint}`;
  console.log(`🚀 API Request: ${options.method || 'GET'} ${url}`);

  try {
    // Don't set Content-Type for FormData - let fetch handle it
    const isFormData = options.body instanceof FormData;
    const headers = isFormData
      ? { ...options.headers } // No Content-Type for FormData
      : { 'Content-Type': 'application/json', ...options.headers };

    const response = await fetch(url, {
      ...options,
      headers,
      mode: 'cors', // Explicitly set CORS mode
      credentials: 'include', // Include credentials for CORS
    });

    console.log(`✅ API Response: ${response.status} ${url}`);

    if (!response.ok) {
      const errorText = await response.text();
      console.error(`❌ HTTP Error: ${response.status} - ${errorText}`);
      throw new Error(`HTTP ${response.status}: ${errorText}`);
    }

    return await response.json();
  } catch (error) {
    console.error(`❌ API Error: ${url}`, error);

    // Check if it's a CORS error
    if (error instanceof TypeError && error.message.includes('fetch')) {
      console.error('❌ CORS Error: Check if backend is running and CORS is configured');
      throw new Error('CORS Error: Unable to connect to backend. Please ensure the backend is running on http://localhost:8000');
    }

    throw error;
  }
}

// API endpoints
export const api = {
  // Document endpoints
  uploadDocument: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);

    console.log('📤 Uploading file:', file.name, 'Size:', file.size);
    console.log('📤 FormData entries:', Array.from(formData.entries()));

    return await apiCall('/documents/upload', {
      method: 'POST',
      body: formData,
      // Don't set Content-Type header - let fetch handle it for FormData
    });
  },

  listDocuments: async () => {
    return await apiCall('/documents/list');
  },

  getDocument: async (documentId: string) => {
    return await apiCall(`/documents/${documentId}`);
  },

  deleteDocument: async (documentId: string) => {
    return await apiCall(`/documents/${documentId}`, {
      method: 'DELETE',
    });
  },

  getDocumentCount: async () => {
    return await apiCall('/documents/');
  },

  // Health check
  healthCheck: async () => {
    return await apiCall('/health');
  },

  // Backend Ollama status
  ollamaStatus: async () => {
    // Prefer chat endpoint; documents has one too
    try {
      return await apiCall('/chat/ollama-status');
    } catch (e) {
      return await apiCall('/documents/ollama-status');
    }
  },

  // Notify dev via backend
  notifyDev: async (message?: string) => {
    const body = message ? { message } : {};
    return await apiCall('/documents/notify-dev', {
      method: 'POST',
      body: JSON.stringify(body),
    });
  },

  // Chat endpoints
  sendMessage: async (message: string, documentIds: string[] = []) => {
    return await apiCall('/chat/message', {
      method: 'POST',
      body: JSON.stringify({
        message,
        document_ids: documentIds,
      }),
    });
  },

  getChatHistory: async (sessionId: string = 'default_session') => {
    return await apiCall(`/chat/history/${sessionId}`);
  },
};

export default api;
