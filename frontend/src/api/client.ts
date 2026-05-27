import axios from 'axios';
import { useAuthStore } from '../stores/authStore';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1/';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true, // Send httpOnly cookies along with every request
  headers: {
    'Content-Type': 'application/json',
  },
});

// Response interceptor for automatic token refresh on 401
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    // If it's a 401, not a retry, and not an auth endpoint, attempt silent token refresh
    if (
      error.response?.status === 401 && 
      !originalRequest._retry && 
      originalRequest.url && 
      !originalRequest.url.includes('auth/token')
    ) {
      originalRequest._retry = true;
      try {
        logger.info("Access token expired. Attempting silent refresh...");
        await axios.post(
          `${apiClient.defaults.baseURL}auth/token/refresh/`, 
          {}, 
          { withCredentials: true }
        );
        return apiClient(originalRequest);
      } catch (refreshError) {
        logger.error("Token refresh failed. Redirecting to login.");
        useAuthStore.getState().logout();
        return Promise.reject(refreshError);
      }
    }
    return Promise.reject(error);
  }
);

// Minimal console logging helper
const logger = {
  info: (msg: string) => console.log(`[API INFO] ${msg}`),
  error: (msg: string) => console.error(`[API ERROR] ${msg}`),
};
