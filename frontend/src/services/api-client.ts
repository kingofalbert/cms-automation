/**
 * API client for backend communication with authentication.
 */

import axios, { AxiosInstance, AxiosRequestConfig, AxiosError } from 'axios';
import type { APIError as APIErrorType } from '../types/api';
import { logAPIError } from '../utils/errorLogger';

/**
 * Base API URL from environment variables.
 */
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * API error response interface.
 * @deprecated Use APIError from '../types/api' instead
 */
export interface APIError extends APIErrorType {}

/**
 * Type alias for the error type used by Axios.
 */
type APIAxiosError = AxiosError<APIErrorType>;

/**
 * Create configured axios instance for API requests.
 */
function createAPIClient(): AxiosInstance {
  const client = axios.create({
    baseURL: API_BASE_URL,
    timeout: 30000, // 30 seconds
    headers: {
      'Content-Type': 'application/json',
    },
  });

  // Request interceptor: Add authentication token
  client.interceptors.request.use(
    (config) => {
      // Get token from localStorage
      const token = localStorage.getItem('auth_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    },
    (error) => Promise.reject(error)
  );

  // Response interceptor: Handle errors
  client.interceptors.response.use(
    (response) => response,
    (error: APIAxiosError) => {
      // Extract error details
      const status = error.response?.status || 0;
      const message = error.response?.data?.message || error.message;
      const requestId = error.response?.data?.request_id;
      const endpoint = error.config?.url || 'unknown';

      // Log API error
      logAPIError(endpoint, status, message, {
        request_id: requestId,
        method: error.config?.method,
        data: error.config?.data,
      });

      // Handle 401 Unauthorized - clear token and redirect to login
      if (status === 401) {
        localStorage.removeItem('auth_token');
        // TODO: Redirect to CMS login page
        window.location.href = '/login';
      }

      return Promise.reject(error);
    }
  );

  return client;
}

/**
 * Global API client instance.
 */
export const apiClient = createAPIClient();

/**
 * Set authentication token.
 */
export function setAuthToken(token: string): void {
  localStorage.setItem('auth_token', token);
}

/**
 * Clear authentication token.
 */
export function clearAuthToken(): void {
  localStorage.removeItem('auth_token');
}

/**
 * Get authentication token.
 */
export function getAuthToken(): string | null {
  return localStorage.getItem('auth_token');
}

/**
 * Check if user is authenticated.
 */
export function isAuthenticated(): boolean {
  return !!getAuthToken();
}

/**
 * API client methods.
 */
export const api = {
  /**
   * GET request.
   */
  get: <T = unknown>(url: string, config?: AxiosRequestConfig) =>
    apiClient.get<T>(url, config).then((res) => res.data),

  /**
   * POST request.
   */
  post: <T = unknown>(url: string, data?: unknown, config?: AxiosRequestConfig) =>
    apiClient.post<T>(url, data, config).then((res) => res.data),

  /**
   * PUT request.
   */
  put: <T = unknown>(url: string, data?: unknown, config?: AxiosRequestConfig) =>
    apiClient.put<T>(url, data, config).then((res) => res.data),

  /**
   * PATCH request.
   */
  patch: <T = unknown>(url: string, data?: unknown, config?: AxiosRequestConfig) =>
    apiClient.patch<T>(url, data, config).then((res) => res.data),

  /**
   * DELETE request.
   */
  delete: <T = unknown>(url: string, config?: AxiosRequestConfig) =>
    apiClient.delete<T>(url, config).then((res) => res.data),
};
