import axios from 'axios';

// Base API URL is configurable via VITE_API_BASE_URL (Vite) or REACT_APP_API_URL (CRA).
// Falls back to production backend URL when deployed on Render Static Site (preventing relative 404s),
// or to '/api' (proxied by Vite dev server to http://localhost:8000) when running locally.
const resolveApiBaseUrl = () => {
  // 1. Vite build-time environment variable (VITE_API_URL or VITE_API_BASE_URL)
  const envVite = import.meta.env?.VITE_API_URL || import.meta.env?.VITE_API_BASE_URL;
  if (envVite && typeof envVite === 'string' && envVite.trim() !== '') {
    return envVite.trim();
  }

  // 2. CRA style environment variable
  if (typeof process !== 'undefined' && process.env?.REACT_APP_API_URL) {
    return process.env.REACT_APP_API_URL.trim();
  }

  // 3. Browser runtime overrides (window or localStorage)
  if (typeof window !== 'undefined') {
    if (window.__KNOWLEDGEGUARD_API_URL__ && typeof window.__KNOWLEDGEGUARD_API_URL__ === 'string') {
      return window.__KNOWLEDGEGUARD_API_URL__.trim();
    }
    try {
      const stored = window.localStorage?.getItem('VITE_API_URL') || window.localStorage?.getItem('VITE_API_BASE_URL');
      if (stored && stored.trim() !== '') {
        return stored.trim();
      }
    } catch (_) {}


    // 4. Production Render Fallback:
    // When running on Render (e.g. knowledgeguardai-1.onrender.com), avoid relative paths
    // which target the static host and throw 404s. Fall back to backend instance:
    const hostname = window.location.hostname;
    if (hostname && hostname !== 'localhost' && hostname !== '127.0.0.1') {
      // If frontend is 'knowledgeguardai-1.onrender.com', backend is 'knowledgeguardai.onrender.com'
      if (hostname.includes('knowledgeguardai-1')) {
        return 'https://knowledgeguardai.onrender.com/api';
      }
      return 'https://knowledgeguard-backend.onrender.com/api';
    }
  }

  // 5. Local development default (proxied by Vite to http://localhost:8000)
  return '/api';
};

const rawBaseUrl = resolveApiBaseUrl();
const API_BASE_URL = rawBaseUrl.endsWith('/') ? rawBaseUrl.slice(0, -1) : rawBaseUrl;

console.info(`[KnowledgeGuard AI] Active API Base URL: ${API_BASE_URL}`);

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
