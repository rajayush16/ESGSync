import { apiClient } from './api';
import type { DashboardOverview, EmissionsByMonth } from '@/types';

export const analyticsService = {
  async getOverview(): Promise<DashboardOverview> {
    const { data } = await apiClient.get('/analytics/overview/');
    return data;
  },

  async getEmissionsByMonth(params?: { year?: number; scope?: string }): Promise<EmissionsByMonth[]> {
    const { data } = await apiClient.get('/analytics/emissions-by-month/', { params });
    return data;
  },

  async getUploadStats(): Promise<unknown> {
    const { data } = await apiClient.get('/analytics/upload-stats/');
    return data;
  },

  async getSuspiciousSummary(): Promise<unknown> {
    const { data } = await apiClient.get('/analytics/suspicious-summary/');
    return data;
  },
};
