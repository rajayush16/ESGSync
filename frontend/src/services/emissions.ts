import { apiClient } from './api';
import type { EmissionRecord, EmissionSummary, PaginatedResponse } from '@/types';

export const emissionsService = {
  async list(params?: Record<string, unknown>): Promise<PaginatedResponse<EmissionRecord>> {
    const { data } = await apiClient.get('/emissions/', { params });
    return data;
  },

  async get(id: string): Promise<EmissionRecord> {
    const { data } = await apiClient.get(`/emissions/${id}/`);
    return data;
  },

  async getSummary(): Promise<EmissionSummary[]> {
    const { data } = await apiClient.get('/emissions/summary/');
    return data;
  },

  async approve(id: string): Promise<EmissionRecord> {
    const { data } = await apiClient.post(`/emissions/${id}/approve/`);
    return data;
  },

  async reject(id: string, reason: string): Promise<EmissionRecord> {
    const { data } = await apiClient.post(`/emissions/${id}/reject/`, { reason });
    return data;
  },

  async lockForAudit(id: string): Promise<EmissionRecord> {
    const { data } = await apiClient.post(`/emissions/${id}/lock-for-audit/`);
    return data;
  },
};
