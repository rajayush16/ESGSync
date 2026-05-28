import { format, parseISO, formatDistanceToNow } from 'date-fns';

export function formatDate(dateStr: string | null | undefined): string {
  if (!dateStr) return '—';
  try {
    return format(parseISO(dateStr), 'dd MMM yyyy');
  } catch {
    return dateStr;
  }
}

export function formatDateTime(dateStr: string | null | undefined): string {
  if (!dateStr) return '—';
  try {
    return format(parseISO(dateStr), 'dd MMM yyyy, HH:mm');
  } catch {
    return dateStr;
  }
}

export function formatRelativeTime(dateStr: string | null | undefined): string {
  if (!dateStr) return '—';
  try {
    return formatDistanceToNow(parseISO(dateStr), { addSuffix: true });
  } catch {
    return dateStr;
  }
}

export function formatCO2e(kg: string | number | null | undefined): string {
  if (kg === null || kg === undefined) return '—';
  const num = typeof kg === 'string' ? parseFloat(kg) : kg;
  if (isNaN(num)) return '—';
  if (num >= 1000) {
    return `${(num / 1000).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} t CO₂e`;
  }
  return `${num.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} kg CO₂e`;
}

export function formatNumber(value: string | number | null | undefined, decimals = 0): string {
  if (value === null || value === undefined) return '—';
  const num = typeof value === 'string' ? parseFloat(value) : value;
  if (isNaN(num)) return '—';
  return num.toLocaleString(undefined, {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function formatPercentage(value: number): string {
  return `${value.toFixed(1)}%`;
}

const SCOPE_COLORS: Record<string, string> = {
  SCOPE_1: 'text-orange-600 bg-orange-50',
  SCOPE_2: 'text-blue-600 bg-blue-50',
  SCOPE_3: 'text-purple-600 bg-purple-50',
};

const STATUS_COLORS: Record<string, string> = {
  UPLOADED: 'text-neutral-600 bg-neutral-100',
  VALIDATING: 'text-blue-600 bg-blue-50',
  NORMALIZED: 'text-indigo-600 bg-indigo-50',
  REVIEW_PENDING: 'text-amber-600 bg-amber-50',
  APPROVED: 'text-success-700 bg-success-50',
  REJECTED: 'text-danger-600 bg-danger-50',
  LOCKED_FOR_AUDIT: 'text-neutral-700 bg-neutral-200',
  FAILED: 'text-danger-700 bg-danger-100',
};

const VALIDATION_COLORS: Record<string, string> = {
  PASSED: 'text-success-700 bg-success-50',
  WARNING: 'text-warning-700 bg-warning-50',
  FAILED: 'text-danger-600 bg-danger-50',
  PENDING: 'text-neutral-600 bg-neutral-100',
};

const DECISION_COLORS: Record<string, string> = {
  APPROVED: 'text-success-700 bg-success-50',
  REJECTED: 'text-danger-600 bg-danger-50',
  ESCALATED: 'text-warning-700 bg-warning-50',
  PENDING: 'text-neutral-600 bg-neutral-100',
};

export function getScopeColor(scope: string): string {
  return SCOPE_COLORS[scope] ?? 'text-neutral-600 bg-neutral-100';
}

export function getStatusColor(status: string): string {
  return STATUS_COLORS[status] ?? 'text-neutral-600 bg-neutral-100';
}

export function getValidationColor(status: string): string {
  return VALIDATION_COLORS[status] ?? 'text-neutral-600 bg-neutral-100';
}

export function getDecisionColor(decision: string): string {
  return DECISION_COLORS[decision] ?? 'text-neutral-600 bg-neutral-100';
}
