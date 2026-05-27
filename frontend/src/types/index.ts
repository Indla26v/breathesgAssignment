export interface Tenant {
  id: string;
  name: string;
  slug: string;
  created_at: string;
  is_active: boolean;
}

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: 'ANALYST' | 'TENANT_ADMIN' | 'PLATFORM_ADMIN';
  tenant: string;
  tenant_name: string;
  tenant_slug: string;
  created_at: string;
}

export interface Batch {
  id: string;
  source_type: 'SAP' | 'UTILITY' | 'TRAVEL';
  status: 'QUEUED' | 'INGESTING' | 'NORMALIZING' | 'PENDING_REVIEW' | 'PARTIAL_FAILURE' | 'APPROVED' | 'LOCKED' | 'FAILED';
  original_filename: string;
  file_ref: string;
  uploaded_by: string | null;
  uploaded_by_email: string;
  uploaded_by_name: string;
  uploaded_at: string;
  record_count: number | null;
  flagged_count: number | null;
  approved_count: number | null;
  error_message: string;
  parser_version: string;
  metadata: any;
}

export interface AnomalyFlag {
  code: string;
  severity: 'WARNING' | 'ERROR';
  message: string;
  field: string;
}

export interface ApprovalEvent {
  id: string;
  record: string;
  analyst: string;
  analyst_name: string;
  analyst_email: string;
  action: 'APPROVED' | 'REJECTED' | 'FLAGGED' | 'EDITED' | 'COMMENT';
  note: string;
  previous_value: any;
  timestamp: string;
}

export interface NormalizedRecord {
  id: string;
  tenant: string;
  batch: string;
  batch_filename: string;
  raw_record: string | null;
  raw_payload: any;
  parse_error: string;
  source_type: 'SAP' | 'UTILITY' | 'TRAVEL';
  activity_type: string;
  scope: 'SCOPE_1' | 'SCOPE_2' | 'SCOPE_3';
  quantity: string;
  unit: string;
  canonical_quantity: string;
  canonical_unit: string;
  period_start: string;
  period_end: string;
  facility_id: string;
  facility_name: string;
  country_code: string;
  origin_iata: string;
  destination_iata: string;
  distance_km: string | null;
  distance_inferred: boolean;
  source_system: string;
  source_batch_ref: string;
  ingest_timestamp: string;
  parser_version: string;
  status: 'PENDING_REVIEW' | 'APPROVED' | 'REJECTED' | 'LOCKED' | 'SUPERSEDED';
  anomaly_flags: AnomalyFlag[];
  is_edited: boolean;
  edit_history: any[];
  approval_events: ApprovalEvent[];
  created_at: string;
  updated_at: string;
}

export interface AuditLog {
  id: string;
  tenant: string;
  batch: string | null;
  actor: string | null;
  actor_email: string;
  actor_name: string;
  action: string;
  record_snapshot: any;
  metadata: any;
  timestamp: string;
}

export interface DashboardSummary {
  pending_batches: number;
  records_awaiting_review: number;
  flagged_records: number;
  locked_records: number;
  by_scope: {
    scope_1: number;
    scope_2: number;
    scope_3: number;
  };
  by_source: {
    sap: number;
    utility: number;
    travel: number;
  };
}
