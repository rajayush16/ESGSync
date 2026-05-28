import { apiClient } from './api';
import type { PaginatedResponse, ReviewTask } from '@/types';

export const reviewsService = {
  async list(params?: Record<string, unknown>): Promise<PaginatedResponse<ReviewTask>> {
    const { data } = await apiClient.get('/reviews/', { params });
    return data;
  },

  async get(id: string): Promise<ReviewTask> {
    const { data } = await apiClient.get(`/reviews/${id}/`);
    return data;
  },

  async approve(id: string, reason?: string): Promise<ReviewTask> {
    const { data } = await apiClient.post(`/reviews/${id}/approve/`, { reason: reason ?? '' });
    return data;
  },

  async reject(id: string, reason: string): Promise<ReviewTask> {
    const { data } = await apiClient.post(`/reviews/${id}/reject/`, { reason });
    return data;
  },

  async escalate(id: string, reason?: string): Promise<ReviewTask> {
    const { data } = await apiClient.post(`/reviews/${id}/escalate/`, { reason: reason ?? '' });
    return data;
  },

  async assign(id: string, assignedTo: string): Promise<ReviewTask> {
    const { data } = await apiClient.post(`/reviews/${id}/assign/`, { assigned_to: assignedTo });
    return data;
  },

  async addComment(id: string, body: string, isInternal?: boolean): Promise<void> {
    await apiClient.post(`/reviews/${id}/comments/`, { body, is_internal: isInternal ?? false });
  },
};
