import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Batch } from '../../types';
import { FileText, Calendar, User, ArrowRight, Loader2 } from 'lucide-react';

interface BatchListProps {
  batches?: Batch[];
  isLoading: boolean;
}

const statusBadgeClass: Record<string, string> = {
  QUEUED: 'badge status-queued',
  INGESTING: 'badge status-ingesting',
  NORMALIZING: 'badge status-normalizing',
  PENDING_REVIEW: 'badge status-pending',
  PARTIAL_FAILURE: 'badge status-partial',
  APPROVED: 'badge status-approved',
  LOCKED: 'badge status-locked',
  FAILED: 'badge status-failed',
};

const statusLabel: Record<string, string> = {
  QUEUED: 'Queued',
  INGESTING: 'Ingesting',
  NORMALIZING: 'Normalizing',
  PENDING_REVIEW: 'Pending Review',
  PARTIAL_FAILURE: 'Partial Failure',
  APPROVED: 'Approved',
  LOCKED: 'Locked',
  FAILED: 'Failed',
};

const sourceBadgeClass: Record<string, string> = {
  SAP: 'badge badge-sap',
  UTILITY: 'badge badge-utility',
  TRAVEL: 'badge badge-travel',
};

const sourceLabel: Record<string, string> = {
  SAP: 'SAP Fuel',
  UTILITY: 'Utility',
  TRAVEL: 'Concur',
};

export const BatchList: React.FC<BatchListProps> = ({ batches, isLoading }) => {
  const navigate = useNavigate();

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleString(undefined, {
      dateStyle: 'medium',
      timeStyle: 'short',
    });
  };

  if (isLoading) {
    return (
      <div className="batch-table-empty card">
        <Loader2 size={28} className="animate-spin" style={{ color: 'var(--primary)' }} />
        <p style={{ marginTop: 8 }}>Loading activity batches…</p>
      </div>
    );
  }

  if (!batches || batches.length === 0) {
    return (
      <div className="batch-table-empty card">
        <FileText size={40} />
        <h3>No Ingestion Batches Found</h3>
        <p>Get started by uploading your first SAP material export, utility spreadsheet, or corporate travel report.</p>
      </div>
    );
  }

  return (
    <div className="batch-table-wrapper">
      <div style={{ overflowX: 'auto' }}>
        <table className="data-table">
          <thead>
            <tr>
              <th>Source</th>
              <th>Filename</th>
              <th>Uploaded</th>
              <th>Records</th>
              <th>Flagged</th>
              <th>Status</th>
              <th style={{ textAlign: 'right' }}>Action</th>
            </tr>
          </thead>
          <tbody>
            {batches.map((batch) => (
              <tr
                key={batch.id}
                onClick={() => navigate(`/batches/${batch.id}`)}
                style={{ cursor: 'pointer' }}
              >
                <td>
                  <span className={sourceBadgeClass[batch.source_type] || 'badge badge-neutral'}>
                    {sourceLabel[batch.source_type] || batch.source_type}
                  </span>
                </td>
                <td style={{ maxWidth: 220 }}>
                  <div className="batch-row-filename truncate">{batch.original_filename}</div>
                  <div className="batch-row-version">v{batch.parser_version}</div>
                </td>
                <td style={{ whiteSpace: 'nowrap' }}>
                  <div className="batch-row-date">
                    <Calendar size={12} />
                    {formatDate(batch.uploaded_at)}
                  </div>
                  <div className="batch-row-uploader">
                    <User size={10} />
                    {batch.uploaded_by_name || 'System'}
                  </div>
                </td>
                <td style={{ fontWeight: 600, color: 'var(--text-secondary)' }}>
                  {batch.record_count ?? '—'}
                </td>
                <td>
                  {batch.flagged_count !== null ? (
                    batch.flagged_count > 0 ? (
                      <span className="batch-row-flagged">{batch.flagged_count}</span>
                    ) : (
                      <span style={{ color: 'var(--text-muted)' }}>0</span>
                    )
                  ) : (
                    <span style={{ color: 'var(--text-muted)' }}>—</span>
                  )}
                </td>
                <td>
                  <span className={statusBadgeClass[batch.status] || 'badge badge-neutral'}>
                    {statusLabel[batch.status] || batch.status}
                  </span>
                </td>
                <td style={{ textAlign: 'right' }}>
                  <button className="batch-row-action-btn">
                    <ArrowRight size={14} />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
