import clsx from 'clsx';
import { getDecisionColor, getScopeColor, getStatusColor, getValidationColor } from '@/utils/formatters';

interface BadgeProps {
  children: React.ReactNode;
  variant?: 'default' | 'status' | 'scope' | 'validation' | 'decision';
  value?: string;
  className?: string;
}

export function Badge({ children, variant = 'default', value, className }: BadgeProps) {
  let colorClass = 'text-neutral-600 bg-neutral-100';

  if (value) {
    if (variant === 'status') colorClass = getStatusColor(value);
    else if (variant === 'scope') colorClass = getScopeColor(value);
    else if (variant === 'validation') colorClass = getValidationColor(value);
    else if (variant === 'decision') colorClass = getDecisionColor(value);
  }

  return (
    <span className={clsx('badge', colorClass, className)}>
      {children}
    </span>
  );
}

const SCOPE_LABELS: Record<string, string> = {
  SCOPE_1: 'Scope 1',
  SCOPE_2: 'Scope 2',
  SCOPE_3: 'Scope 3',
};

export function ScopeBadge({ scope }: { scope: string }) {
  return (
    <Badge variant="scope" value={scope}>
      {SCOPE_LABELS[scope] ?? scope}
    </Badge>
  );
}

export function StatusBadge({ status }: { status: string }) {
  const labels: Record<string, string> = {
    UPLOADED: 'Uploaded',
    VALIDATING: 'Validating',
    NORMALIZED: 'Normalized',
    REVIEW_PENDING: 'Pending Review',
    APPROVED: 'Approved',
    REJECTED: 'Rejected',
    LOCKED_FOR_AUDIT: 'Locked',
    FAILED: 'Failed',
  };
  return (
    <Badge variant="status" value={status}>
      {labels[status] ?? status}
    </Badge>
  );
}

export function ValidationBadge({ status }: { status: string }) {
  return (
    <Badge variant="validation" value={status}>
      {status}
    </Badge>
  );
}

export function DecisionBadge({ decision }: { decision: string }) {
  return (
    <Badge variant="decision" value={decision}>
      {decision}
    </Badge>
  );
}
