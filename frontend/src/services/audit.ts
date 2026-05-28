import { apiClient } from './api';
import type { AuditLog, PaginatedResponse } from '@/types';

export const auditService = {
  async list(params?: Record<string, unknown>): Promise<PaginatedResponse<AuditLog>> {
    const { data } = await apiClient.get('/audit/', { params });
    return data;
  },

  async getEntityHistory(entityType: string, entityId: string): Promise<AuditLog[]> {
    const { data } = await apiClient.get(`/audit/entity/${entityType}/${entityId}/`);
    return data;
  },
};
