import { useParams, Link } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { ArrowLeft, CheckCircle, Lock, XCircle } from 'lucide-react';
import { useState } from 'react';
import { emissionsService } from '@/services/emissions';
import { auditService } from '@/services/audit';
import { PageLoading } from '@/components/common/LoadingSpinner';
import { ErrorAlert } from '@/components/common/ErrorAlert';
import { ScopeBadge, StatusBadge } from '@/components/common/Badge';
import { formatCO2e, formatDate, formatDateTime } from '@/utils/formatters';
import { extractErrorMessage } from '@/services/api';

export function RecordDetailsPage() {
  const { recordId } = useParams<{ recordId: string }>();
  const queryClient = useQueryClient();
  const [rejectReason, setRejectReason] = useState('');
  const [showRejectForm, setShowRejectForm] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  const { data: record, isLoading, error } = useQuery({
    queryKey: ['emission-record', recordId],
    queryFn: () => emissionsService.get(recordId!),
  });

  const { data: history } = useQuery({
    queryKey: ['audit-history', 'EmissionRecord', recordId],
    queryFn: () => auditService.getEntityHistory('EmissionRecord', recordId!),
    enabled: !!record,
  });

  const approveMutation = useMutation({
    mutationFn: () => emissionsService.approve(recordId!),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['emission-record', recordId] }),
    onError: (err) => setActionError(extractErrorMessage(err)),
  });

  const rejectMutation = useMutation({
    mutationFn: () => emissionsService.reject(recordId!, rejectReason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['emission-record', recordId] });
      setShowRejectForm(false);
      setRejectReason('');
    },
    onError: (err) => setActionError(extractErrorMessage(err)),
  });

  const lockMutation = useMutation({
    mutationFn: () => emissionsService.lockForAudit(recordId!),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['emission-record', recordId] }),
    onError: (err) => setActionError(extractErrorMessage(err)),
  });

  if (isLoading) return <PageLoading />;
  if (error) return <ErrorAlert message={extractErrorMessage(error)} />;
  if (!record) return null;

  const sourceFields = Object.entries(record.source_data ?? {}).filter(
    ([k]) => !k.startsWith('emission_') && !k.startsWith('anomaly') && k !== 'co2e_kg'
  );

  return (
    <div className="max-w-3xl space-y-5">
      <div className="flex items-center gap-3">
        <Link to="/emissions" className="text-neutral-500 hover:text-neutral-800">
          <ArrowLeft className="w-5 h-5" />
        </Link>
        <div className="flex-1">
          <h1 className="text-lg font-bold text-neutral-900">Emission Record</h1>
          <p className="text-xs text-neutral-400 font-mono mt-0.5">{record.id}</p>
        </div>
        <StatusBadge status={record.status} />
      </div>

      {actionError && <ErrorAlert message={actionError} dismissible />}

      {/* Actions */}
      {record.status === 'REVIEW_PENDING' && (
        <div className="flex gap-2">
          <button
            className="btn-primary"
            onClick={() => approveMutation.mutate()}
            disabled={approveMutation.isPending}
          >
            <CheckCircle className="w-4 h-4" />
            {approveMutation.isPending ? 'Approving…' : 'Approve'}
          </button>
          <button
            className="btn-secondary"
            onClick={() => setShowRejectForm((v) => !v)}
          >
            <XCircle className="w-4 h-4" />
            Reject
          </button>
        </div>
      )}
      {record.status === 'APPROVED' && (
        <button
          className="btn-secondary"
          onClick={() => lockMutation.mutate()}
          disabled={lockMutation.isPending}
        >
          <Lock className="w-4 h-4" />
          {lockMutation.isPending ? 'Locking…' : 'Lock for Audit'}
        </button>
      )}

      {showRejectForm && (
        <div className="card p-4 space-y-3">
          <label className="label">Rejection Reason</label>
          <textarea
            className="input resize-none h-20"
            value={rejectReason}
            onChange={(e) => setRejectReason(e.target.value)}
            placeholder="Explain why this record is being rejected…"
          />
          <div className="flex gap-2">
            <button
              className="btn-danger"
              disabled={!rejectReason.trim() || rejectMutation.isPending}
              onClick={() => rejectMutation.mutate()}
            >
              {rejectMutation.isPending ? 'Rejecting…' : 'Confirm Rejection'}
            </button>
            <button className="btn-ghost" onClick={() => setShowRejectForm(false)}>Cancel</button>
          </div>
        </div>
      )}

      {record.rejection_reason && (
        <div className="p-3 rounded-md bg-danger-50 border border-danger-100 text-sm text-danger-700">
          <strong>Rejection reason:</strong> {record.rejection_reason}
        </div>
      )}

      {/* Core Details */}
      <div className="card p-5">
        <h2 className="text-sm font-semibold text-neutral-700 mb-4">Emission Details</h2>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
          <div>
            <p className="text-xs text-neutral-500">Scope</p>
            <div className="mt-1"><ScopeBadge scope={record.scope} /></div>
          </div>
          <div>
            <p className="text-xs text-neutral-500">Category</p>
            <p className="font-medium mt-0.5">{record.category_display}</p>
          </div>
          <div>
            <p className="text-xs text-neutral-500">CO₂e</p>
            <p className="font-bold text-lg mt-0.5">{formatCO2e(record.co2e_kg)}</p>
          </div>
          <div>
            <p className="text-xs text-neutral-500">Period Start</p>
            <p className="font-medium mt-0.5">{formatDate(record.reporting_period_start)}</p>
          </div>
          <div>
            <p className="text-xs text-neutral-500">Period End</p>
            <p className="font-medium mt-0.5">{formatDate(record.reporting_period_end)}</p>
          </div>
          <div>
            <p className="text-xs text-neutral-500">Version</p>
            <p className="font-medium mt-0.5">v{record.version}</p>
          </div>
          {record.approved_by_name && (
            <div>
              <p className="text-xs text-neutral-500">Approved by</p>
              <p className="font-medium mt-0.5">{record.approved_by_name}</p>
            </div>
          )}
          {record.approved_at && (
            <div>
              <p className="text-xs text-neutral-500">Approved at</p>
              <p className="font-medium mt-0.5">{formatDateTime(record.approved_at)}</p>
            </div>
          )}
        </div>
      </div>

      {/* Source Data */}
      <div className="card p-5">
        <h2 className="text-sm font-semibold text-neutral-700 mb-4">Normalized Source Data</h2>
        <div className="grid grid-cols-2 gap-3">
          {sourceFields.map(([key, value]) => (
            <div key={key}>
              <p className="text-xs text-neutral-400 font-mono">{key}</p>
              <p className="text-sm text-neutral-800 font-medium mt-0.5 break-all">
                {value !== null && value !== undefined ? String(value) : <span className="text-neutral-300">—</span>}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* Audit History */}
      {history && history.length > 0 && (
        <div className="card p-5">
          <h2 className="text-sm font-semibold text-neutral-700 mb-4">Change History</h2>
          <div className="space-y-3">
            {history.map((log) => (
              <div key={log.id} className="flex items-start gap-3 text-sm">
                <div className="w-1.5 h-1.5 rounded-full bg-neutral-300 mt-1.5 shrink-0" />
                <div>
                  <p className="text-neutral-700">{log.description}</p>
                  <p className="text-xs text-neutral-400 mt-0.5">
                    {log.performed_by_name ?? 'System'} · {formatDateTime(log.created_at)}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
