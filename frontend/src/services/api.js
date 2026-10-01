import axios from 'axios';

// Base API URL is configurable via VITE_API_BASE_URL in production (Render)
// In local development, defaults to '/api' which is proxied to http://localhost:8000 by Vite
const rawBaseUrl = import.meta.env.VITE_API_BASE_URL || '/api';
const API_BASE_URL = rawBaseUrl.endsWith('/') ? rawBaseUrl.slice(0, -1) : rawBaseUrl;

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 60000, // 60s timeout to allow for LLM and agent investigations
});

// Response interceptor for clear developer & user notifications on network or cold start issues
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (!error.response) {
      console.warn(
        'KnowledgeGuard AI backend unreachable. If deployed on Render free tier, the web service may take ~30-50s to wake from hibernation.',
        error.message
      );
    }
    return Promise.reject(error);
  }
);


export const api = {
  // System Health
  getHealth: async () => {
    const res = await apiClient.get('/health');
    return res.data;
  },

  // Dashboard
  getDashboardStats: async () => {
    const res = await apiClient.get('/dashboard/stats');
    return res.data;
  },
  seedSampleDocuments: async () => {
    const res = await apiClient.post('/dashboard/seed-samples');
    return res.data;
  },

  // Documents
  getDocuments: async (skip = 0, limit = 100) => {
    const res = await apiClient.get(`/documents?skip=${skip}&limit=${limit}`);
    return res.data;
  },
  getDocumentById: async (id) => {
    const res = await apiClient.get(`/documents/${id}`);
    return res.data;
  },
  uploadDocument: async (formData) => {
    const res = await apiClient.post('/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return res.data;
  },
  deleteDocument: async (id) => {
    const res = await apiClient.delete(`/documents/${id}`);
    return res.data;
  },

  // Investigations
  investigateClaim: async (claim) => {
    const res = await apiClient.post('/investigate', { claim });
    return res.data;
  },
  getInvestigations: async (skip = 0, limit = 100) => {
    const res = await apiClient.get(`/investigations?skip=${skip}&limit=${limit}`);
    return res.data;
  },
  getInvestigationById: async (id) => {
    const res = await apiClient.get(`/investigations/${id}`);
    return res.data;
  },
  updateReviewStatus: async (id, status) => {
    const res = await apiClient.patch(`/investigations/${id}/review-status`, { status });
    return res.data;
  },

  // Evaluation Benchmarks
  runEvaluation: async () => {
    const res = await apiClient.post('/evaluation/run');
    return res.data;
  },
  getEvaluationSummary: async () => {
    const res = await apiClient.get('/evaluation/summary');
    return res.data;
  },
  getEvaluationResults: async () => {
    const res = await apiClient.get('/evaluation/results');
    return res.data;
  },
  getConfusionMatrix: async () => {
    const res = await apiClient.get('/evaluation/confusion-matrix');
    return res.data;
  },
  exportEvaluationReport: async () => {
    const res = await apiClient.get('/evaluation/export', { responseType: 'blob' });
    return res.data;
  },
};

export default api;
