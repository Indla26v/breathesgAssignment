import React, { useState, useEffect } from 'react';
import { NormalizedRecord } from '../../types';
import { AnomalyBadge } from './AnomalyBadge';
import { ScopeBadge } from './ScopeBadge';
import {
  useEditRecord, useApproveRecord, useRejectRecord, useFlagRecord
} from '../../hooks/useRecords';
import {
  X, Check, AlertTriangle, Eye, History, Edit,
  MessageSquare, TrendingUp, MapPin, Clock, Loader2,
  Lock as LockIcon
} from 'lucide-react';

interface RawPayloadDrawerProps {
  record: NormalizedRecord | null;
  onClose: () => void;
}

const statusBadgeClass: Record<string, string> = {
  PENDING_REVIEW: 'badge status-pending',
  APPROVED: 'badge status-approved',
  REJECTED: 'badge status-rejected',
  LOCKED: 'badge status-locked',
};

export const RawPayloadDrawer: React.FC<RawPayloadDrawerProps> = ({ record, onClose }) => {
  const [activeTab, setActiveTab] = useState<'info' | 'raw' | 'history'>('info');
  const [editMode, setEditMode] = useState(false);
  const [qtyInput, setQtyInput] = useState('');
  const [unitInput, setUnitInput] = useState('');
  const [noteInput, setNoteInput] = useState('');
  const [actionNote, setActionNote] = useState('');
  const [showRejectForm, setShowRejectForm] = useState(false);
  const [showFlagForm, setShowFlagForm] = useState(false);

  const editMutation = useEditRecord();
  const approveMutation = useApproveRecord();
  const rejectMutation = useRejectRecord();
  const flagMutation = useFlagRecord();

  useEffect(() => {
    if (record) {
      setQtyInput(record.quantity);
      setUnitInput(record.unit);
      setNoteInput('');
      setActionNote('');
      setEditMode(false);
      setShowRejectForm(false);
      setShowFlagForm(false);
    }
  }, [record]);

  if (!record) return null;

  const handleEditSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!noteInput) return;
    try {
      await editMutation.mutateAsync({ id: record.id, quantity: parseFloat(qtyInput), unit: unitInput, note: noteInput });
      setEditMode(false);
    } catch (err) {
      console.error(err);
    }
  };

  const handleApprove = async () => {
    try {
      await approveMutation.mutateAsync({ id: record.id, note: actionNote });
      setActionNote('');
    } catch (err) {
      console.error(err);
    }
  };

  const handleReject = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!actionNote) return;
    try {
      await rejectMutation.mutateAsync({ id: record.id, note: actionNote });
      setActionNote('');
      setShowRejectForm(false);
    } catch (err) {
      console.error(err);
    }
  };

  const handleFlag = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!actionNote) return;
    try {
      await flagMutation.mutateAsync({ id: record.id, note: actionNote });
      setActionNote('');
      setShowFlagForm(false);
    } catch (err) {
      console.error(err);
    }
  };

  const isMutating = editMutation.isPending || approveMutation.isPending || rejectMutation.isPending || flagMutation.isPending;

  return (
    <div className="drawer-overlay">
      <div className="drawer-backdrop" onClick={onClose} />
      <div className="drawer-panel">
        {/* Header */}
        <div className="drawer-header">
          <div>
            <div className="drawer-header-label">Review Record Detail</div>
            <div className="drawer-header-title">{record.activity_type.replace(/_/g, ' ')}</div>
          </div>
          <button onClick={onClose} className="drawer-close">
            <X size={14} />
          </button>
        </div>

        {/* Tabs */}
        <div className="drawer-tabs">
          <button onClick={() => setActiveTab('info')} className={`drawer-tab ${activeTab === 'info' ? 'active' : ''}`}>
            <Eye size={13} /> Details
          </button>
          <button onClick={() => setActiveTab('raw')} className={`drawer-tab ${activeTab === 'raw' ? 'active' : ''}`}>
            <MessageSquare size={13} /> Raw JSON
          </button>
          <button onClick={() => setActiveTab('history')} className={`drawer-tab ${activeTab === 'history' ? 'active' : ''}`}>
            <History size={13} /> Timeline ({record.approval_events.length})
          </button>
        </div>

        {/* Content */}
        <div className="drawer-content">
          {isMutating && (
            <div className="drawer-loading-overlay">
              <Loader2 size={28} className="animate-spin" style={{ color: 'var(--primary)' }} />
            </div>
          )}

          {/* Tab 1: Info */}
          {activeTab === 'info' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              {/* Badges */}
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <ScopeBadge scope={record.scope} />
                <span className={statusBadgeClass[record.status] || 'badge badge-neutral'}>
                  {record.status.replace(/_/g, ' ')}
                </span>
              </div>

              {/* Flags */}
              {record.anomaly_flags.length > 0 && (
                <div className="record-flags-box">
                  <div className="record-flags-title">
                    <AlertTriangle size={12} /> Screening Flags Detected
                  </div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                    {record.anomaly_flags.map((flag, idx) => (
                      <AnomalyBadge key={idx} code={flag.code} />
                    ))}
                  </div>
                  <div className="record-flags-list">
                    {record.anomaly_flags.map((flag, idx) => (
                      <div key={idx} className="record-flag-item">
                        <strong>{flag.code.replace(/_/g, ' ')}:</strong> {flag.message}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Quantities */}
              <div className="record-qty-grid">
                <div className="record-qty-box">
                  <div className="record-qty-label" style={{ color: 'var(--text-muted)' }}>Reported Amount</div>
                  <div className="record-qty-value" style={{ color: 'var(--text)' }}>
                    {record.quantity}<span className="record-qty-unit" style={{ color: 'var(--text-muted)' }}>{record.unit}</span>
                  </div>
                </div>
                <div className="record-qty-box" style={{ background: 'var(--primary-light)', borderColor: 'rgba(13,147,115,0.15)' }}>
                  <div className="record-qty-label" style={{ color: 'var(--primary)' }}>Canonical Amount</div>
                  <div className="record-qty-value" style={{ color: 'var(--primary)' }}>
                    {record.canonical_quantity}<span className="record-qty-unit" style={{ opacity: 0.7 }}>{record.canonical_unit}</span>
                  </div>
                </div>
              </div>

              {/* Fields */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                <div className="record-section-title"><TrendingUp size={13} /> Normalization Identity</div>
                <div className="record-detail-grid">
                  <div className="record-detail-item"><span>Activity Type</span><p>{record.activity_type}</p></div>
                  <div className="record-detail-item"><span>Source System</span><p>{record.source_system}</p></div>
                </div>

                <div className="record-section-title"><Clock size={13} /> Temporal Range</div>
                <div className="record-detail-grid">
                  <div className="record-detail-item"><span>Start Date</span><p>{record.period_start}</p></div>
                  <div className="record-detail-item"><span>End Date</span><p>{record.period_end}</p></div>
                </div>

                <div className="record-section-title"><MapPin size={13} /> Geographic & Site Context</div>
                <div className="record-detail-grid">
                  <div className="record-detail-item"><span>Facility ID</span><p>{record.facility_id || 'unassigned'}</p></div>
                  <div className="record-detail-item"><span>Facility Name</span><p>{record.facility_name || 'unknown'}</p></div>
                  {record.country_code && (
                    <div className="record-detail-item"><span>Country Code</span><p>{record.country_code}</p></div>
                  )}
                </div>

                {record.source_type === 'TRAVEL' && (
                  <>
                    <div className="record-section-title">Travel Parameters</div>
                    <div className="record-detail-grid">
                      {record.origin_iata && <div className="record-detail-item"><span>Origin IATA</span><p>{record.origin_iata}</p></div>}
                      {record.destination_iata && <div className="record-detail-item"><span>Destination IATA</span><p>{record.destination_iata}</p></div>}
                      {record.distance_km && <div className="record-detail-item"><span>Distance (KM)</span><p>{record.distance_km}</p></div>}
                    </div>
                  </>
                )}
              </div>

              {/* Edit form */}
              {record.status !== 'LOCKED' && (
                <div className="record-edit-box">
                  {!editMode ? (
                    <button onClick={() => setEditMode(true)} className="btn btn-secondary" style={{ width: '100%' }}>
                      <Edit size={13} /> Correct Ingested Values
                    </button>
                  ) : (
                    <form onSubmit={handleEditSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                      <div className="record-edit-grid">
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                          <label>Quantity</label>
                          <input type="number" step="any" value={qtyInput} onChange={(e) => setQtyInput(e.target.value)} required />
                        </div>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                          <label>Unit</label>
                          <input type="text" value={unitInput} onChange={(e) => setUnitInput(e.target.value)} required />
                        </div>
                      </div>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                        <label>Audit Correction Note</label>
                        <input type="text" placeholder="Explain reason for correction…" value={noteInput} onChange={(e) => setNoteInput(e.target.value)} required />
                      </div>
                      <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
                        <button type="button" onClick={() => setEditMode(false)} className="btn btn-secondary">Cancel</button>
                        <button type="submit" className="btn btn-primary">Save Corrections</button>
                      </div>
                    </form>
                  )}
                </div>
              )}
            </div>
          )}

          {/* Tab 2: Raw JSON */}
          {activeTab === 'raw' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12, height: '100%' }}>
              <p style={{ fontSize: '0.75rem' }}>
                Below is the original row parsed from the source system file, prior to any normalizations:
              </p>
              <pre className="raw-json-viewer">{JSON.stringify(record.raw_payload, null, 2)}</pre>
            </div>
          )}

          {/* Tab 3: Timeline */}
          {activeTab === 'history' && (
            <div>
              {record.approval_events.length === 0 ? (
                <div className="table-empty-state">
                  <p>No events recorded for this record yet.</p>
                </div>
              ) : (
                <div className="timeline">
                  {record.approval_events.map((event) => (
                    <div key={event.id} className="timeline-event">
                      <div
                        className="timeline-dot"
                        style={{
                          background:
                            event.action === 'APPROVED' ? 'var(--primary)' :
                            event.action === 'REJECTED' ? 'var(--danger)' :
                            event.action === 'FLAGGED' ? 'var(--warning)' :
                            'var(--scope-3)'
                        }}
                      />
                      <div className="timeline-event-header">
                        <span className="timeline-event-action">{event.action} by {event.analyst_name}</span>
                        <span className="timeline-event-time">{new Date(event.timestamp).toLocaleString()}</span>
                      </div>
                      {event.note && (
                        <div className="timeline-event-note">&ldquo;{event.note}&rdquo;</div>
                      )}
                      {event.previous_value && (
                        <pre className="timeline-event-diff">{JSON.stringify(event.previous_value, null, 2)}</pre>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="drawer-footer">
          {record.status !== 'LOCKED' && !editMode && (
            <>
              {!showRejectForm && !showFlagForm ? (
                <div className="drawer-action-row">
                  <button onClick={() => setShowFlagForm(true)} className="btn btn-secondary" style={{ color: 'var(--warning)' }}>
                    <AlertTriangle size={13} /> Flag
                  </button>
                  <button onClick={() => setShowRejectForm(true)} className="btn btn-danger">
                    <X size={13} /> Reject
                  </button>
                  <button onClick={handleApprove} className="btn btn-primary">
                    <Check size={13} /> Approve
                  </button>
                </div>
              ) : (
                <form
                  onSubmit={showRejectForm ? handleReject : handleFlag}
                  className="drawer-action-form"
                >
                  <div className="drawer-action-form-header">
                    <span className="drawer-action-form-label">
                      {showRejectForm ? 'Reject Record' : 'Flag for Query'}
                    </span>
                    <button
                      type="button"
                      onClick={() => { setShowRejectForm(false); setShowFlagForm(false); setActionNote(''); }}
                      className="btn btn-ghost"
                      style={{ padding: '4px 8px', fontSize: '0.75rem' }}
                    >
                      Cancel
                    </button>
                  </div>
                  <input
                    type="text"
                    placeholder={showRejectForm ? 'Reason for rejection…' : 'Detail anomalous flag issue…'}
                    value={actionNote}
                    onChange={(e) => setActionNote(e.target.value)}
                    required
                  />
                  <button type="submit" className={`btn ${showRejectForm ? 'btn-danger' : 'btn-primary'}`} style={{ width: '100%' }}>
                    Confirm {showRejectForm ? 'Rejection' : 'Flagging'}
                  </button>
                </form>
              )}
            </>
          )}
          {record.status === 'LOCKED' && (
            <div className="drawer-locked-text">
              <LockIcon size={14} /> Locked in Audit Log
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
