import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const authAPI = {
  login: (username, password) => api.post('/auth/login', { username, password }),
  register: (username, email, password) => api.post('/auth/register', { username, email, password }),
  getMe: () => api.get('/auth/me'),
};

export const imagesAPI = {
  upload: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/images/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  detect: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/images/detect', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
};

export const liveAPI = {
  getStatus: () => api.get('/live/status'),
  start: (source = 'esp32', model = 'medium') => api.post('/live/start', {}, { params: { source, model } }),
  stop: () => api.post('/live/stop'),
  getFrame: () => api.get('/live/frame', { responseType: 'arraybuffer' }),
  getRecentDefects: (limit = 10) => api.get('/live/recent-defects', { params: { limit } }),
  recordDefect: (defect) => api.post('/live/record-defect', null, { params: defect }),
};

export const dashboardAPI = {
  getStats: () => api.get('/dashboard/stats'),
  getDefects: (skip = 0, limit = 20, defectType = null, source = null) => {
    const params = { skip, limit };
    if (defectType) params.defect_type = defectType;
    if (source) params.source = source;
    return api.get('/dashboard/defects', { params });
  },
  getTypeDistribution: () => api.get('/dashboard/chart/type-distribution'),
  getDailyDefects: (days = 7) => api.get('/dashboard/chart/daily-defects', { params: { days } }),
  getSourceDistribution: () => api.get('/dashboard/chart/source-distribution'),
  getConfidenceDistribution: () => api.get('/dashboard/chart/confidence-distribution'),
  getPendingDefects: (skip = 0, limit = 50) => api.get('/dashboard/pending', { params: { skip, limit } }),
  getPendingStats: () => api.get('/dashboard/pending/stats'),
  addPendingDefect: (defect) => api.post('/dashboard/pending/add', null, { params: defect }),
};

export default api;
