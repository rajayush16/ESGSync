// ─── Auth ────────────────────────────────────────────────────────────────────

export interface AuthUser {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  organization_id: string | null;
  organization_name: string | null;
}

export interface LoginResponse {
  access: string;
  refresh: string;
  user: AuthUser;
}

// ─── Enums ───────────────────────────────────────────────────────────────────

export type UserRole = 'ADMIN' | 'DATA_MANAGER' | 'ANALYST' | 'AUDITOR' | 'VIEWER';

export type IngestionStatus =
  | 'UPLOADED'
  | 'VALIDATING'
  | 'NORMALIZED'
  | 'REVIEW_PENDING'
  | 'APPROVED'
  | 'REJECTED'
  | 'LOCKED_FOR_AUDIT'
  | 'FAILED';

export type DataSourceType = 'SAP_FUEL' | 'UTILITY_ELECTRICITY' | 'CORPORATE_TRAVEL';

export type EmissionScope = 'SCOPE_1' | 'SCOPE_2' | 'SCOPE_3';

export type EmissionCategory =
  | 'STATIONARY_COMBUSTION'
  | 'MOBILE_COMBUSTION'
  | 'FUGITIVE_EMISSIONS'
  | 'PURCHASED_ELECTRICITY'
  | 'PURCHASED_HEAT'
  | 'BUSINESS_TRAVEL'
  | 'EMPLOYEE_COMMUTING'
  | 'UPSTREAM_TRANSPORT'
  | 'WASTE_OPERATIONS'
  | 'FUEL_ENERGY';

export type ValidationStatus = 'PASSED' | 'WARNING' | 'FAILED' | 'PENDING';

export type ReviewDecision = 'APPROVED' | 'REJECTED' | 'ESCALATED' | 'PENDING';

export type AuditAction =
  | 'UPLOAD_CREATED'
  | 'RECORD_CREATED'
  | 'RECORD_UPDATED'
  | 'VALIDATION_RUN'
  | 'NORMALIZATION_RUN'
  | 'REVIEW_ASSIGNED'
  | 'RECORD_APPROVED'
  | 'RECORD_REJECTED'
  | 'RECORD_ESCALATED'
  | 'RECORD_LOCKED'
  | 'ANOMALY_FLAGGED'
  | 'USER_LOGIN'
  | 'USER_LOGOUT'
  | 'EXPORT_CREATED';

// ─── Organization ─────────────────────────────────────────────────────────────

export interface Organization {
  id: string;
  name: string;
  slug: string;
  industry_sector: string;
  country: string;
  is_active: boolean;
  user_count: number;
  created_at: string;
}

export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  organization: string;
  organization_name: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
}

// ─── Ingestion ────────────────────────────────────────────────────────────────

export interface DataSource {
  id: string;
  name: string;
  source_type: DataSourceType;
  description: string;
  is_active: boolean;
  created_at: string;
}

export interface UploadSession {
  id: string;
  original_filename: string;
  file_size_mb: number;
  status: IngestionStatus;
  data_source: string;
  data_source_name: string;
  data_source_type: DataSourceType;
  uploaded_by: string;
  uploaded_by_name: string;
  total_rows: number;
  processed_rows: number;
  passed_rows: number;
  failed_rows: number;
  warning_rows: number;
  success_rate: number;
  error_message: string;
  notes: string;
  processing_started_at: string | null;
  processing_completed_at: string | null;
  created_at: string;
}

export interface ValidationError {
  id: string;
  field_name: string;
  error_code: string;
  message: string;
  severity: ValidationStatus;
}

export interface RawRecord {
  id: string;
  row_number: number;
  raw_data: Record<string, unknown>;
  normalized_data: Record<string, unknown> | null;
  validation_status: ValidationStatus;
  is_suspicious: boolean;
  suspicion_reasons: string[];
  processing_notes: string;
  validation_errors: ValidationError[];
  created_at: string;
}

// ─── Emissions ────────────────────────────────────────────────────────────────

export interface EmissionRecord {
  id: string;
  scope: EmissionScope;
  scope_display: string;
  category: EmissionCategory;
  category_display: string;
  co2e_kg: string;
  co2e_mt: string;
  status: IngestionStatus;
  status_display: string;
  reporting_period_start: string | null;
  reporting_period_end: string | null;
  facility: string | null;
  facility_name: string | null;
  upload_session: string;
  upload_session_filename: string;
  approved_by: string | null;
  approved_by_name: string | null;
  approved_at: string | null;
  rejection_reason: string;
  version: number;
  source_data: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface EmissionSummary {
  scope: EmissionScope;
  scope_display: string;
  total_co2e_kg: string;
  total_co2e_mt: string;
  record_count: number;
}

// ─── Reviews ──────────────────────────────────────────────────────────────────

export interface ReviewTask {
  id: string;
  emission_record: string;
  emission_record_detail: EmissionRecord;
  decision: ReviewDecision;
  decision_at: string | null;
  decision_by: string | null;
  decision_by_name: string | null;
  assigned_to: string | null;
  assigned_to_name: string | null;
  comments: string;
  comments_list: ReviewComment[];
  priority: 'LOW' | 'MEDIUM' | 'HIGH' | 'URGENT';
  due_date: string | null;
  is_suspicious: boolean;
  created_at: string;
  updated_at: string;
}

export interface ReviewComment {
  id: string;
  author: string;
  author_name: string;
  body: string;
  is_internal: boolean;
  created_at: string;
}

// ─── Audit ────────────────────────────────────────────────────────────────────

export interface AuditLog {
  id: string;
  action: AuditAction;
  entity_type: string;
  entity_id: string;
  description: string;
  previous_value: Record<string, unknown> | null;
  new_value: Record<string, unknown> | null;
  metadata: Record<string, unknown>;
  performed_by: string | null;
  performed_by_name: string | null;
  performed_by_email: string | null;
  ip_address: string | null;
  source_file: string;
  created_at: string;
}

// ─── Analytics ────────────────────────────────────────────────────────────────

export interface DashboardOverview {
  total_co2e_kg: number;
  total_co2e_mt: number;
  scope_breakdown_kg: Record<EmissionScope, number>;
  pending_review_count: number;
  suspicious_record_count: number;
  failed_validation_count: number;
  recent_uploads: Array<{
    id: string;
    original_filename: string;
    status: IngestionStatus;
    total_rows: number;
    created_at: string;
  }>;
}

export interface EmissionsByMonth {
  period: string;
  scope_1_co2e_kg: number;
  scope_2_co2e_kg: number;
  scope_3_co2e_kg: number;
  total_co2e_kg: number;
}

// ─── API Pagination ──────────────────────────────────────────────────────────

export interface PaginatedResponse<T> {
  count: number;
  page: number;
  page_size: number;
  num_pages: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface ApiError {
  error: {
    code: string;
    message: string;
    details?: unknown;
  };
}
