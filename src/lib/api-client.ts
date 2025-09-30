// Simple fetch-based API client
const API_BASE_URL = 'http://localhost:8000';

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
    
    return await apiCall('/api/documents/upload', {
      method: 'POST',
      body: formData,
      // Don't set Content-Type header - let fetch handle it for FormData
    });
  },

  listDocuments: async () => {
    return await apiCall('/api/documents/list');
  },

  getDocument: async (documentId: string) => {
    return await apiCall(`/api/documents/${documentId}`);
  },

  deleteDocument: async (documentId: string) => {
    return await apiCall(`/api/documents/${documentId}`, {
      method: 'DELETE',
    });
  },

  getDocumentCount: async () => {
    return await apiCall('/api/documents/');
  },

  // Health check
  healthCheck: async () => {
    return await apiCall('/api/health');
  },

  // Chat endpoints
  sendMessage: async (message: string, documentIds: string[] = []) => {
    return await apiCall('/api/chat/message', {
      method: 'POST',
      body: JSON.stringify({
        message,
        document_ids: documentIds,
      }),
    });
  },

  getChatHistory: async (sessionId: string = 'default_session') => {
    return await apiCall(`/api/chat/history/${sessionId}`);
  },
};

export default api;
