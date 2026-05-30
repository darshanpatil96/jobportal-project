/**
 * ARTISAN API Client — Candidate Portal
 *
 * Axios instance with JWT authentication and automatic token refresh.
 * All candidate API calls go through this client.
 */

import axios from 'axios';
import { useAuthStore } from '../stores/authStore';

const API_BASE = import.meta.env.VITE_API_URL || '/api/v1';

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Attach access token to every request
api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Auto-refresh on 401
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refresh = useAuthStore.getState().refreshToken;
        if (!refresh) throw new Error('No refresh token');

        const { data } = await axios.post(`${API_BASE}/auth/token/refresh/`, {
          refresh,
        });

        useAuthStore.getState().setTokens(data.access, refresh);
        originalRequest.headers.Authorization = `Bearer ${data.access}`;
        return api(originalRequest);
      } catch {
        useAuthStore.getState().logout();
        window.location.href = '/login';
      }
    }

    return Promise.reject(error);
  }
);

export default api;
