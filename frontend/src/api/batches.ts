import { apiClient } from './client';
import { Batch, DashboardSummary, AuditLog } from '../types';

export const getBatches = async (params?: { status?: string; source_type?: string }): Promise<Batch[]> => {
  const response = await apiClient.get('batches/', { params });
  return response.data.data;
};

export const getBatch = async (id: string): Promise<Batch> => {
  const response = await apiClient.get(`batches/${id}/`);
  return response.data.data;
};

export const getBatchStatus = async (id: string): Promise<any> => {
  const response = await apiClient.get(`batches/${id}/status/`);
  return response.data.data;
};

export const uploadBatch = async (
  file: File, 
  sourceType: string, 
  metadata: any
): Promise<Batch & { task_id: string }> => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('source_type', sourceType);
  formData.append('metadata', JSON.stringify(metadata));

  const response = await apiClient.post('batches/', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data.data;
};

export const signOffBatch = async (id: string): Promise<any> => {
  const response = await apiClient.post(`batches/${id}/sign-off/`);
  return response.data.data;
};

export const getBatchAuditLog = async (id: string): Promise<AuditLog[]> => {
  const response = await apiClient.get(`batches/${id}/audit-log/`);
  return response.data.data;
};

export const getDashboardSummary = async (): Promise<DashboardSummary> => {
  const response = await apiClient.get('dashboard/summary/');
  return response.data.data;
};
