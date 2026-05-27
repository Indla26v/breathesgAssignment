import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getBatches, getBatch, getBatchStatus, uploadBatch, signOffBatch, getBatchAuditLog } from '../api/batches';

export const useBatches = (filters?: { status?: string; source_type?: string }) => {
  return useQuery({
    queryKey: ['batches', filters],
    queryFn: () => getBatches(filters),
    refetchInterval: (query) => {
      // Auto-refetch every 10 seconds if any batch is in an active processing state
      const batches = query.state.data;
      if (batches && Array.isArray(batches)) {
        const isProcessing = batches.some(
          (b) => b.status === 'QUEUED' || b.status === 'INGESTING' || b.status === 'NORMALIZING'
        );
        return isProcessing ? 10000 : false;
      }
      return false;
    },
  });
};

export const useBatch = (id: string) => {
  return useQuery({
    queryKey: ['batch', id],
    queryFn: () => getBatch(id),
    enabled: !!id,
  });
};

export const useBatchStatus = (id: string, isProcessing: boolean) => {
  return useQuery({
    queryKey: ['batch-status', id],
    queryFn: () => getBatchStatus(id),
    enabled: !!id && isProcessing,
    refetchInterval: isProcessing ? 2000 : false, // Poll status every 2 seconds if processing
  });
};

export const useUploadBatch = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ file, sourceType, metadata }: { file: File; sourceType: string; metadata: any }) =>
      uploadBatch(file, sourceType, metadata),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['batches'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard-summary'] });
    },
  });
};

export const useSignOffBatch = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => signOffBatch(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ['batch', id] });
      queryClient.invalidateQueries({ queryKey: ['batches'] });
      queryClient.invalidateQueries({ queryKey: ['records', id] });
      queryClient.invalidateQueries({ queryKey: ['audit-log', id] });
      queryClient.invalidateQueries({ queryKey: ['dashboard-summary'] });
    },
  });
};

export const useBatchAuditLog = (id: string) => {
  return useQuery({
    queryKey: ['audit-log', id],
    queryFn: () => getBatchAuditLog(id),
    enabled: !!id,
  });
};
