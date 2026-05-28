import { apiClient } from './api';
import type { DataSource, PaginatedResponse, RawRecord, UploadSession } from '@/types';

export const uploadsService = {
  async listDataSources(): Promise<PaginatedResponse<DataSource>> {
    const { data } = await apiClient.get('/uploads/sources/');
    return data;
  },

  async listSessions(params?: Record<string, unknown>): Promise<PaginatedResponse<UploadSession>> {
    const { data } = await apiClient.get('/uploads/sessions/', { params });
    return data;
  },

  async getSession(id: string): Promise<UploadSession> {
    const { data } = await apiClient.get(`/uploads/sessions/${id}/`);
    return data;
  },

  async uploadFile(
    dataSourceId: string,
    file: File,
    notes?: string,
    onProgress?: (pct: number) => void,
  ): Promise<UploadSession> {
    const form = new FormData();
    form.append('data_source', dataSourceId);
    form.append('file', file);
    if (notes) form.append('notes', notes);

    const { data } = await apiClient.post('/uploads/sessions/upload/', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (e) => {
        if (onProgress && e.total) {
          onProgress(Math.round((e.loaded / e.total) * 100));
        }
      },
    });
    return data;
  },

  async getSessionRecords(
    sessionId: string,
    params?: { validation_status?: string; suspicious?: boolean; page?: number },
  ): Promise<PaginatedResponse<RawRecord>> {
    const { data } = await apiClient.get(`/uploads/sessions/${sessionId}/records/`, { params });
    return data;
  },

  async reprocessSession(sessionId: string): Promise<{ task_id: string; message: string }> {
    const { data } = await apiClient.post(`/uploads/sessions/${sessionId}/reprocess/`);
    return data;
  },

  async listSuspiciousRecords(params?: Record<string, unknown>): Promise<PaginatedResponse<RawRecord>> {
    const { data } = await apiClient.get('/uploads/suspicious/', { params });
    return data;
  },
};
