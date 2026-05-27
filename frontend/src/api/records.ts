import { apiClient } from './client';
import { NormalizedRecord } from '../types';

export interface GetRecordsParams {
  status?: string;
  scope?: string;
  has_flags?: string;
}

export const getBatchRecords = async (
  batchId: string, 
  params?: GetRecordsParams
): Promise<NormalizedRecord[]> => {
  const response = await apiClient.get(`batches/${batchId}/records/`, { params });
  // If response contains pagination envelope, return data array
  if (response.data && response.data.data) {
    return response.data.data;
  }
  return response.data;
};

export const getRecordDetail = async (id: string): Promise<NormalizedRecord> => {
  const response = await apiClient.get(`records/${id}/`);
  return response.data.data;
};

export const editRecord = async (
  id: string, 
  data: { quantity: number; unit: string; note: string }
): Promise<NormalizedRecord> => {
  const response = await apiClient.patch(`records/${id}/`, data);
  return response.data.data;
};

export const approveRecord = async (id: string, note?: string): Promise<NormalizedRecord> => {
  const response = await apiClient.post(`records/${id}/approve/`, { note });
  return response.data.data;
};

export const rejectRecord = async (id: string, note: string): Promise<NormalizedRecord> => {
  const response = await apiClient.post(`records/${id}/reject/`, { note });
  return response.data.data;
};

export const flagRecord = async (id: string, note: string): Promise<NormalizedRecord> => {
  const response = await apiClient.post(`records/${id}/flag/`, { note });
  return response.data.data;
};
