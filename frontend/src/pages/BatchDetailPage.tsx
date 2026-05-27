import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useBatch, useSignOffBatch, useBatchAuditLog } from '../hooks/useBatches';
import { useBatchRecords } from '../hooks/useRecords';
import { ScopeBadge } from '../components/review/ScopeBadge';
import { AnomalyBadge } from '../components/review/AnomalyBadge';
import { RawPayloadDrawer } from '../components/review/RawPayloadDrawer';
import { NormalizedRecord } from '../types';
import {
  ArrowLeft, Calendar, User, Database, FileSpreadsheet,
  AlertTriangle, Lock, Loader2, CheckCircle, FileText
} from 'lucide-react';

const statusBadgeClass: Record<string, string> = {
  PENDING_REVIEW: 'badge status-pending',
  APPROVED: 'badge status-approved',
  REJECTED: 'badge status-rejected',
  LOCKED: 'badge status-locked',
};

export const BatchDetailPage: React.FC = () => {
  const { id = '' } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState<'ALL' | 'PENDING_REVIEW' | 'FLAGGED' | 'APPROVED' | 'REJECTED'>('ALL');
  const [selectedRecord, setSelectedRecord] = useState<NormalizedRecord | null>(null);

  const { data: batch, isLoading: isBatchLoading } = useBatch(id);

  const recordFilters = {
    status: activeTab === 'ALL' || activeTab === 'FLAGGED' ? undefined : activeTab,
    has_flags: activeTab === 'FLAGGED' ? 'true' : undefined
  };
  const { data: records, isLoading: isRecordsLoading } = useBatchRecords(id, recordFilters);

  const { data: auditLogs } = useBatchAuditLog(id);
  const signOffMutation = useSignOffBatch();

  const handleSignOff = async () => {
    if (!window.confirm('Are you sure you want to sign off this batch? This will lock all approved records and write an immutable entry to the audit log.')) return;
    try {
      await signOffMutation.mutateAsync(id);
    } catch (err: any) {
      alert(err.response?.data?.errors?.[0]?.message || 'Sign-off failed.');
    }
  };

  if (isBatchLoading) {
    return (
      <div className="loading-fullpage">
        <Loader2 size={28} className="animate-spin" />
      </div>
    );
  }

  if (!batch) {
    return (
      <div className="table-empty-state card">
        <p>Batch not found or you do not have permissions to access it.</p>
      </div>
    );
  }

  const showSignOffPanel = batch.status !== 'LOCKED';

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20, paddingBottom: showSignOffPanel ? 80 : 0 }}>
      {/* Back */}
      <button onClick={() => navigate('/dashboard')} className="btn btn-secondary" style={{ width: 'fit-content' }}>
        <ArrowLeft size={14} /> Back to Dashboard
      </button>

      {/* Header */}
      <div className="card batch-header-panel">
        <div>
          <div className="batch-header-info">
            <div className="batch-header-icon">
              {batch.source_type === 'SAP' ? <Database size={18} /> : <FileSpreadsheet size={18} />}
            </div>
            <div>
              <h3 className="batch-header-title">{batch.original_filename}</h3>
              <div className="batch-header-id">Batch ID: {batch.id}</div>
            </div>
          </div>
          <div className="batch-meta">
            <span className="batch-meta-item"><Calendar size={12} /> {new Date(batch.uploaded_at).toLocaleString()}</span>
            <span className="batch-meta-item"><User size={12} /> {batch.uploaded_by_name}</span>
            <span className="batch-meta-version">v{batch.parser_version}</span>
          </div>
        </div>

        <div className="batch-stats-grid">
          <div className="batch-stat">
            <div className="batch-stat-label">Total Rows</div>
            <div className="batch-stat-value" style={{ color: 'var(--text)' }}>{batch.record_count ?? '—'}</div>
          </div>
          <div className="batch-stat">
            <div className="batch-stat-label">Flagged</div>
            <div className="batch-stat-value" style={{ color: 'var(--danger)' }}>{batch.flagged_count ?? '—'}</div>
          </div>
          <div className="batch-stat">
            <div className="batch-stat-label">Approved</div>
            <div className="batch-stat-value" style={{ color: 'var(--primary)' }}>{batch.approved_count ?? '0'}</div>
          </div>
        </div>
      </div>

      {/* Tabs & Records */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        <div className="tab-bar">
          {(['ALL', 'PENDING_REVIEW', 'FLAGGED', 'APPROVED', 'REJECTED'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => { setActiveTab(tab); setSelectedRecord(null); }}
              className={`tab-item ${activeTab === tab ? 'active' : ''}`}
            >
              {tab.replace(/_/g, ' ')}
            </button>
          ))}
        </div>

        {isRecordsLoading ? (
          <div className="table-loading card">
            <Loader2 size={22} className="animate-spin" />
            <span>Loading records…</span>
          </div>
        ) : !records || records.length === 0 ? (
          <div className="card table-empty-state">
            <FileText size={32} />
            <p>No records match filter criteria</p>
          </div>
        ) : (
          <div className="card" style={{ overflow: 'hidden' }}>
            <div style={{ overflowX: 'auto' }}>
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Date/Period</th>
                    <th>Activity Type</th>
                    <th>Scope</th>
                    <th>Facility</th>
                    <th style={{ textAlign: 'right' }}>Reported Qty</th>
                    <th style={{ textAlign: 'right' }}>Canonical Qty</th>
                    <th>Flags</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {records.map((rec) => (
                    <tr
                      key={rec.id}
                      onClick={() => setSelectedRecord(rec)}
                      style={{
                        cursor: 'pointer',
                        background: selectedRecord?.id === rec.id ? 'var(--surface-alt)' : undefined
                      }}
                    >
                      <td style={{ whiteSpace: 'nowrap', fontSize: '0.75rem' }}>
                        {rec.period_start === rec.period_end
                          ? rec.period_start
                          : `${rec.period_start} → ${rec.period_end}`}
                      </td>
                      <td style={{ fontWeight: 500 }}>{rec.activity_type.replace(/_/g, ' ')}</td>
                      <td><ScopeBadge scope={rec.scope} /></td>
                      <td style={{ fontSize: '0.75rem', maxWidth: 140 }} className="truncate">
                        {rec.facility_name || rec.facility_id || 'unassigned'}
                      </td>
                      <td style={{ textAlign: 'right', fontWeight: 600, color: 'var(--text-secondary)' }}>
                        {rec.quantity} <span style={{ fontSize: '0.625rem', color: 'var(--text-muted)' }}>{rec.unit}</span>
                      </td>
                      <td style={{ textAlign: 'right', fontWeight: 700, color: 'var(--primary)' }}>
                        {rec.canonical_quantity} <span style={{ fontSize: '0.625rem', opacity: 0.7 }}>{rec.canonical_unit}</span>
                      </td>
                      <td style={{ maxWidth: 160 }}>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 3, maxHeight: 24, overflow: 'hidden' }}>
                          {rec.anomaly_flags.slice(0, 2).map((flag, idx) => (
                            <AnomalyBadge key={idx} code={flag.code} />
                          ))}
                          {rec.anomaly_flags.length > 2 && (
                            <span className="badge badge-neutral">+{rec.anomaly_flags.length - 2}</span>
                          )}
                          {rec.anomaly_flags.length === 0 && (
                            <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>—</span>
                          )}
                        </div>
                      </td>
                      <td>
                        <span className={statusBadgeClass[rec.status] || 'badge badge-neutral'}>
                          {rec.status.replace(/_/g, ' ')}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {/* Audit Trail */}
      {batch.status === 'LOCKED' && auditLogs && auditLogs.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12, marginTop: 8 }}>
          <h3 style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Lock size={16} style={{ color: 'var(--source-sap)' }} /> Immutable Audit Trail
          </h3>
          <div className="card audit-trail-card">
            {auditLogs.map((log) => (
              <div key={log.id} className="audit-entry">
                <div className="audit-entry-icon">
                  <Lock size={12} />
                </div>
                <div style={{ flex: 1 }}>
                  <div className="audit-entry-header">
                    <span className="audit-entry-action">{log.action.replace(/_/g, ' ')}</span>
                    <span className="audit-entry-time">{new Date(log.timestamp).toLocaleString()}</span>
                  </div>
                  <div className="audit-entry-actor">
                    Executed by <strong>{log.actor_name || 'System'}</strong> ({log.actor_email || 'cron'})
                  </div>
                  {log.metadata && Object.keys(log.metadata).length > 0 && (
                    <pre className="audit-entry-metadata">{JSON.stringify(log.metadata, null, 2)}</pre>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Sign-off footer */}
      {showSignOffPanel && (
        <div className="signoff-footer">
          <div className="signoff-info">
            <AlertTriangle size={18} />
            <div className="signoff-info-text">
              <p>Audit Sign-Off Console</p>
              <p>All rows must be APPROVED or REJECTED before sign-off.</p>
            </div>
          </div>
          <button
            onClick={handleSignOff}
            disabled={signOffMutation.isPending}
            className="btn btn-primary"
          >
            {signOffMutation.isPending ? (
              <><Loader2 size={14} className="animate-spin" /> Locking Batch…</>
            ) : (
              <><CheckCircle size={14} /> Sign Off & Lock Batch</>
            )}
          </button>
        </div>
      )}

      {/* Record Drawer */}
      <RawPayloadDrawer record={selectedRecord} onClose={() => setSelectedRecord(null)} />
    </div>
  );
};
