/**
 * Authentication API Service
 *
 * Provides type-safe methods for authentication and user management.
 */

import { api, setAuthToken, clearAuthToken } from './api-client';
import type { LoginRequest, LoginResponse, User, APIResponse } from '../types/api';

export const authAPI = {
  /**
   * Login with username and password.
   * Stores the authentication token on success.
   */
  login: async (credentials: LoginRequest) => {
    const response = await api.post<APIResponse<LoginResponse>>(
      '/v1/auth/login',
      credentials
    );

    if (response.success && response.data.access_token) {
      setAuthToken(response.data.access_token);
    }

    return response;
  },

  /**
   * Logout and clear authentication token.
   */
  logout: () => {
    clearAuthToken();
    return api.post<APIResponse<void>>('/v1/auth/logout');
  },

  /**
   * Get current authenticated user information.
   */
  getCurrentUser: () => api.get<APIResponse<User>>('/v1/auth/me'),

  /**
   * Refresh authentication token.
   */
  refreshToken: async () => {
    const response = await api.post<
      APIResponse<{
        access_token: string;
        token_type: string;
        expires_in: number;
      }>
    >('/v1/auth/refresh');

    if (response.success && response.data.access_token) {
      setAuthToken(response.data.access_token);
    }

    return response;
  },

  /**
   * Change user password.
   */
  changePassword: (currentPassword: string, newPassword: string) =>
    api.post<APIResponse<void>>('/v1/auth/change-password', {
      current_password: currentPassword,
      new_password: newPassword,
    }),

  /**
   * Request password reset email.
   */
  requestPasswordReset: (email: string) =>
    api.post<APIResponse<void>>('/v1/auth/request-password-reset', { email }),

  /**
   * Reset password with token.
   */
  resetPassword: (token: string, newPassword: string) =>
    api.post<APIResponse<void>>('/v1/auth/reset-password', {
      token,
      new_password: newPassword,
    }),

  /**
   * Verify if current authentication token is valid.
   */
  verifyToken: () => api.get<APIResponse<{ valid: boolean }>>('/v1/auth/verify'),
};
