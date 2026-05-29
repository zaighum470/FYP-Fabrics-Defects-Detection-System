// API service for communicating with the backend
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  register: (userData) => api.post('/api/auth/register', userData),
  login: (loginData) => api.post('/api/auth/login', loginData),
  me: () => api.get('/api/auth/me'),
};

// Image detection API
export const imageAPI = {
  upload: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/api/images/upload', formData);
  },
  detect: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/api/images/detect', formData);
  },
};

// Live stream API
export const liveAPI = {
  start: (source, model) => api.post('/api/live/start', { source, model }),
  stop: () => api.post('/api/live/stop'),
  status: () => api.get('/api/live/status'),
  frame: () => api.get('/api/live/frame', { responseType: 'arraybuffer' }),
  recentDefects: (limit = 10) => api.get(`/api/live/recent-defects?limit=${limit}`),
  recordDefect: (defectData) => api.post('/api/live/record-defect', defectData),
};

// Dashboard API
export const dashboardAPI = {
  getStats: () => api.get('/api/dashboard/stats'),
  getDefects: (params) => api.get('/api/dashboard/defects', { params }),
  getTypeDistribution: () => api.get('/api/dashboard/chart/type-distribution'),
  getDailyDefects: (days = 7) => api.get(`/api/dashboard/chart/daily-defects?days=${days}`),
  getConfidenceDistribution: () => api.get('/api/dashboard/chart/confidence-distribution'),
  getPendingStats: () => api.get('/api/dashboard/pending/stats'),
  getPendingDefects: (params) => api.get('/api/dashboard/pending', { params }),
  addPendingDefect: (defectData) => api.post('/api/dashboard/pending/add', defectData),
  acceptPendingDefect: (defectId) => api.post(`/api/dashboard/pending/${defectId}/accept`),
  deletePendingDefect: (defectId) => api.post(`/api/dashboard/pending/${defectId}/delete`),
  convertAllPending: () => api.post('/api/dashboard/pending/convert-all'),
  discardAllPending: () => api.post('/api/dashboard/pending/discard-all'),
  clearHistory: () => api.post('/api/dashboard/clear-history'),
  resetDefectCount: () => api.post('/api/dashboard/pending/reset-count'),
};

export default api;