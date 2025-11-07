import axios from 'axios';

// Backend API base URL
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Create axios instance with default config
export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 300000, // 5 minutes for RAG+LLaMA analysis (can take 2-4 minutes)
});

// Add response interceptor for debugging
apiClient.interceptors.response.use(
  response => {
    console.log('✅ API Response:', response.config.url);
    return response;
  },
  error => {
    console.error('❌ API Error:', error.config?.url, error.message);
    return Promise.reject(error);
  }
);

// API endpoints
export const API_ENDPOINTS = {
  // Health check
  health: '/api/v1/health',
  
  // Policy analysis
  analyzePolicy: '/api/v1/analyze',
  uploadPolicy: '/api/v1/upload',
  
  // Chat
  chat: '/api/v1/chat',
  createChatSession: '/api/v1/chat/session',
  
  // Dashboard
  getPolicies: '/api/v1/policies',
  getPolicyById: (id: string) => `/api/v1/policies/${id}`,
  getStatistics: '/api/v1/statistics',
};

// API functions
export const api = {
  // Health check
  checkHealth: async () => {
    const response = await apiClient.get(API_ENDPOINTS.health);
    return response.data;
  },

  // Upload and analyze policy
  uploadPolicy: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await apiClient.post(API_ENDPOINTS.uploadPolicy, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 300000, // 5 minutes for RAG+LLaMA (regulation retrieval + LLaMA generation)
    });
    return response.data;
  },

  // Get analysis by ID
  getAnalysis: async (id: string) => {
    const response = await apiClient.get(API_ENDPOINTS.getPolicyById(id));
    return response.data;
  },

  // Chat with AI
  sendChatMessage: async (sessionId: string, message: string, policyContext?: any) => {
    const response = await apiClient.post(API_ENDPOINTS.chat, {
      session_id: sessionId,
      message,
      policy_context: policyContext,
    });
    return response.data;
  },

  // Get all policies
  getAllPolicies: async () => {
    const response = await apiClient.get(API_ENDPOINTS.getPolicies);
    return response.data;
  },

  // Get dashboard statistics
  getStatistics: async () => {
    const response = await apiClient.get(API_ENDPOINTS.getStatistics);
    return response.data;
  },
};
