import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useBatches } from '../hooks/useBatches';
import { getDashboardSummary } from '../api/batches';
import { useQuery } from '@tanstack/react-query';
import { StatsBar } from '../components/dashboard/StatsBar';
import { BatchList } from '../components/dashboard/BatchList';
import { UploadCloud, RefreshCw } from 'lucide-react';

export const DashboardPage: React.FC = () => {
  const navigate = useNavigate();

  const {
    data: summary,
    isLoading: isSummaryLoading,
    refetch: refetchSummary,
    isRefetching: isSummaryRefetching
  } = useQuery({
    queryKey: ['dashboard-summary'],
    queryFn: getDashboardSummary,
  });

  const {
    data: batches,
    isLoading: isBatchesLoading,
    refetch: refetchBatches,
    isRefetching: isBatchesRefetching
  } = useBatches();

  const handleRefresh = () => {
    refetchSummary();
    refetchBatches();
  };

  const isRefreshing = isSummaryRefetching || isBatchesRefetching;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 28 }}>
      {/* Header */}
      <div className="page-header">
        <div className="page-header-text">
          <h2>Ingestion Dashboard</h2>
          <p>Review activity files, track normalization pipelines, and approve audit entries.</p>
        </div>
        <div className="page-header-actions">
          <button
            onClick={handleRefresh}
            disabled={isRefreshing}
            className="btn btn-secondary btn-icon"
            title="Refresh metrics"
          >
            <RefreshCw size={16} className={isRefreshing ? 'animate-spin' : ''} />
          </button>
          <button onClick={() => navigate('/upload')} className="btn btn-primary">
            <UploadCloud size={16} />
            Upload New Batch
          </button>
        </div>
      </div>

      {/* Stats */}
      <StatsBar summary={summary} isLoading={isSummaryLoading} />

      {/* Batch List */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        <div className="section-header">
          <h3>Recent Ingestion Batches</h3>
          <span className="section-header-hint">Auto-refreshes while ingesting</span>
        </div>
        <BatchList batches={batches} isLoading={isBatchesLoading} />
      </div>
    </div>
  );
};
