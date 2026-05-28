import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { FileText } from 'lucide-react';
import { auditService } from '@/services/audit';
import { PageLoading } from '@/components/common/LoadingSpinner';
import { ErrorAlert } from '@/components/common/ErrorAlert';
import { Pagination } from '@/components/common/Pagination';
import { EmptyState } from '@/components/common/EmptyState';
import { formatDateTime } from '@/utils/formatters';
import { extractErrorMessage } from '@/services/api';

const ACTION_COLORS: Record<string, string> = {
  UPLOAD_CREATED: 'bg-blue-100 text-blue-700',
  RECORD_APPROVED: 'bg-success-100 text-success-700',
  RECORD_REJECTED: 'bg-danger-100 text-danger-700',
  RECORD_LOCKED: 'bg-neutral-200 text-neutral-700',
  USER_LOGIN: 'bg-neutral-100 text-neutral-500',
  ANOMALY_FLAGGED: 'bg-amber-100 text-amber-700',
};

export function AuditTimelinePage() {
  const [page, setPage] = useState(1);
  const [actionFilter, setActionFilter] = useState('');

  const { data, isLoading, error } = useQuery({
    queryKey: ['audit-logs', page, actionFilter],
    queryFn: () => auditService.list({ page, action: actionFilter || undefined }),
  });

  if (isLoading) return <PageLoading />;
  if (error) return <ErrorAlert message={extractErrorMessage(error)} />;

  const logs = data?.results ?? [];

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-bold text-neutral-900">Audit Timeline</h1>
        <p className="text-sm text-neutral-500 mt-0.5">
          Immutable audit trail — every significant action recorded
        </p>
      </div>

      {/* Filter */}
      <div>
        <select
          className="input w-56"
          value={actionFilter}
          onChange={(e) => { setActionFilter(e.target.value); setPage(1); }}
        >
          <option value="">All actions</option>
          <option value="UPLOAD_CREATED">Upload Created</option>
          <option value="RECORD_APPROVED">Record Approved</option>
          <option value="RECORD_REJECTED">Record Rejected</option>
          <option value="RECORD_LOCKED">Record Locked</option>
          <option value="ANOMALY_FLAGGED">Anomaly Flagged</option>
          <option value="USER_LOGIN">User Login</option>
          <option value="REVIEW_ASSIGNED">Review Assigned</option>
        </select>
      </div>

      <div className="card">
        {logs.length === 0 ? (
          <EmptyState icon={FileText} title="No audit entries" description="Actions will appear here as they occur." />
        ) : (
          <>
            <div className="divide-y divide-neutral-100">
              {logs.map((log) => (
                <div key={log.id} className="px-5 py-3.5 flex items-start gap-4">
                  <div className="shrink-0 mt-0.5">
                    <span className={`badge text-xs ${ACTION_COLORS[log.action] ?? 'bg-neutral-100 text-neutral-600'}`}>
                      {log.action.replace(/_/g, ' ')}
                    </span>
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-neutral-800">{log.description}</p>
                    <div className="flex items-center gap-3 mt-1">
                      {log.entity_type && (
                        <span className="text-xs text-neutral-400 font-mono">
                          {log.entity_type}:{log.entity_id?.slice(0, 8)}
                        </span>
                      )}
                      {log.performed_by_email && (
                        <span className="text-xs text-neutral-500">{log.performed_by_name ?? log.performed_by_email}</span>
                      )}
                    </div>
                  </div>
                  <div className="shrink-0 text-xs text-neutral-400 whitespace-nowrap">
                    {formatDateTime(log.created_at)}
                  </div>
                </div>
              ))}
            </div>
            {data && (
              <Pagination
                page={data.page}
                numPages={data.num_pages}
                count={data.count}
                pageSize={data.page_size}
                onPageChange={setPage}
              />
            )}
          </>
        )}
      </div>
    </div>
  );
}
