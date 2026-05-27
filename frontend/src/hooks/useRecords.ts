import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getBatchRecords, getRecordDetail, editRecord, approveRecord, rejectRecord, flagRecord } from '../api/records';

export const useBatchRecords = (batchId: string, filters?: { status?: string; scope?: string; has_flags?: string }) => {
  return useQuery({
    queryKey: ['records', batchId, filters],
    queryFn: () => getBatchRecords(batchId, filters),
    enabled: !!batchId,
  });
};

export const useRecordDetail = (id: string) => {
  return useQuery({
    queryKey: ['record', id],
    queryFn: () => getRecordDetail(id),
    enabled: !!id,
  });
};

export const useEditRecord = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, quantity, unit, note }: { id: string; quantity: number; unit: string; note: string }) =>
      editRecord(id, { quantity, unit, note }),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['record', data.id] });
      queryClient.invalidateQueries({ queryKey: ['records', data.batch] });
      queryClient.invalidateQueries({ queryKey: ['batch', data.batch] });
      queryClient.invalidateQueries({ queryKey: ['dashboard-summary'] });
    },
  });
};

export const useApproveRecord = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, note }: { id: string; note?: string }) => approveRecord(id, note),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['record', data.id] });
      queryClient.invalidateQueries({ queryKey: ['records', data.batch] });
      queryClient.invalidateQueries({ queryKey: ['batch', data.batch] });
      queryClient.invalidateQueries({ queryKey: ['dashboard-summary'] });
    },
  });
};

export const useRejectRecord = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, note }: { id: string; note: string }) => rejectRecord(id, note),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['record', data.id] });
      queryClient.invalidateQueries({ queryKey: ['records', data.batch] });
      queryClient.invalidateQueries({ queryKey: ['batch', data.batch] });
      queryClient.invalidateQueries({ queryKey: ['dashboard-summary'] });
    },
  });
};

export const useFlagRecord = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, note }: { id: string; note: string }) => flagRecord(id, note),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['record', data.id] });
      queryClient.invalidateQueries({ queryKey: ['records', data.batch] });
      queryClient.invalidateQueries({ queryKey: ['batch', data.batch] });
      queryClient.invalidateQueries({ queryKey: ['dashboard-summary'] });
    },
  });
};
