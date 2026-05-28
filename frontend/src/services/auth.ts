import { apiClient } from './api';
import type { AuthUser, LoginResponse } from '@/types';

export const authService = {
  async login(email: string, password: string): Promise<LoginResponse> {
    const { data } = await apiClient.post<LoginResponse>('/auth/token/', { email, password });
    localStorage.setItem('access_token', data.access);
    localStorage.setItem('refresh_token', data.refresh);
    return data;
  },

  async logout(): Promise<void> {
    const refresh = localStorage.getItem('refresh_token');
    if (refresh) {
      await apiClient.post('/auth/token/blacklist/', { refresh }).catch(() => {});
    }
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
  },

  async getCurrentUser(): Promise<AuthUser> {
    const { data } = await apiClient.get<AuthUser>('/auth/me/');
    return data;
  },

  async changePassword(currentPassword: string, newPassword: string): Promise<void> {
    await apiClient.put('/auth/change-password/', {
      current_password: currentPassword,
      new_password: newPassword,
    });
  },

  isAuthenticated(): boolean {
    return !!localStorage.getItem('access_token');
  },
};
