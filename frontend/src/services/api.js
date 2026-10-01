import axios from 'axios';

// The Vite dev server proxies /api to http://localhost:8000
const API_BASE_URL = '/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const api = {
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
