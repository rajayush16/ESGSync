import { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { ArrowLeft, AlertTriangle } from 'lucide-react';
import { uploadsService } from '@/services/uploads';
import { PageLoading } from '@/components/common/LoadingSpinner';
import { ErrorAlert } from '@/components/common/ErrorAlert';
import { StatusBadge, ValidationBadge } from '@/components/common/Badge';
import { Pagination } from '@/components/common/Pagination';
import { formatDateTime, formatNumber } from '@/utils/formatters';
import { extractErrorMessage } from '@/services/api';

export function UploadSessionDetailPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const [recordPage, setRecordPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState('');
  const [showSuspicious, setShowSuspicious] = useState(false);

  const { data: session, isLoading, error } = useQuery({
    queryKey: ['upload-session', sessionId],
    queryFn: () => uploadsService.getSession(sessionId!),
    refetchInterval: (query) =>
      query.state.data?.status === 'VALIDATING' || query.state.data?.status === 'UPLOADED'
        ? 3000
        : false,
  });

  const { data: records } = useQuery({
    queryKey: ['session-records', sessionId, recordPage, statusFilter, showSuspicious],
    queryFn: () =>
      uploadsService.getSessionRecords(sessionId!, {
        page: recordPage,
        validation_status: statusFilter || undefined,
        suspicious: showSuspicious || undefined,
      }),
    enabled: !!session,
  });

  if (isLoading) return <PageLoading />;
  if (error) return <ErrorAlert message={extractErrorMessage(error)} />;
  if (!session) return null;

  return (
    <div className="space-y-5">
      <div className="flex items-center gap-3">
        <Link to="/uploads/history" className="text-neutral-500 hover:text-neutral-800">
          <ArrowLeft className="w-5 h-5" />
        </Link>
        <div className="flex-1">
          <h1 className="text-lg font-bold text-neutral-900">{session.original_filename}</h1>
          <p className="text-sm text-neutral-500">{session.data_source_name}</p>
        </div>
        <StatusBadge status={session.status} />
      </div>

      {session.error_message && (
        <ErrorAlert title="Ingestion Error" message={session.error_message} />
      )}

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[
          { label: 'Total Rows', value: formatNumber(session.total_rows) },
          { label: 'Passed', value: formatNumber(session.passed_rows), color: 'text-success-600' },
          { label: 'Warnings', value: formatNumber(session.warning_rows), color: 'text-warning-600' },
          { label: 'Failed', value: formatNumber(session.failed_rows), color: 'text-danger-600' },
        ].map(({ label, value, color }) => (
          <div key={label} className="card px-4 py-3">
            <p className="text-xs text-neutral-500">{label}</p>
            <p className={`text-xl font-bold mt-0.5 ${color ?? 'text-neutral-900'}`}>{value}</p>
          </div>
        ))}
      </div>

      {/* Meta */}
      <div className="card p-4 grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
        <div>
          <p className="text-xs text-neutral-500">Uploaded by</p>
          <p className="font-medium mt-0.5">{session.uploaded_by_name}</p>
        </div>
        <div>
          <p className="text-xs text-neutral-500">Uploaded at</p>
          <p className="font-medium mt-0.5">{formatDateTime(session.created_at)}</p>
        </div>
        <div>
          <p className="text-xs text-neutral-500">Completed at</p>
          <p className="font-medium mt-0.5">{formatDateTime(session.processing_completed_at)}</p>
        </div>
        <div>
          <p className="text-xs text-neutral-500">File size</p>
          <p className="font-medium mt-0.5">{session.file_size_mb} MB</p>
        </div>
        <div>
          <p className="text-xs text-neutral-500">Success rate</p>
          <p className="font-medium mt-0.5">{session.success_rate}%</p>
        </div>
        {session.notes && (
          <div>
            <p className="text-xs text-neutral-500">Notes</p>
            <p className="font-medium mt-0.5">{session.notes}</p>
          </div>
        )}
      </div>

      {/* Records */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-semibold text-neutral-700">Records</h2>
          <div className="flex gap-2">
            <select
              className="input w-40"
              value={statusFilter}
              onChange={(e) => { setStatusFilter(e.target.value); setRecordPage(1); }}
            >
              <option value="">All statuses</option>
              <option value="PASSED">Passed</option>
              <option value="WARNING">Warning</option>
              <option value="FAILED">Failed</option>
            </select>
            <button
              onClick={() => { setShowSuspicious((v) => !v); setRecordPage(1); }}
              className={showSuspicious ? 'btn-primary' : 'btn-secondary'}
            >
              <AlertTriangle className="w-3.5 h-3.5" />
              Suspicious
            </button>
          </div>
        </div>

        <div className="card">
          <div className="table-container rounded-none border-none">
            <table className="table">
              <thead>
                <tr>
                  <th>Row</th>
                  <th>Validation</th>
                  <th>Suspicious</th>
                  <th>Issues</th>
                </tr>
              </thead>
              <tbody>
                {(records?.results ?? []).map((record) => (
                  <tr key={record.id}>
                    <td className="font-mono text-xs">{record.row_number}</td>
                    <td><ValidationBadge status={record.validation_status} /></td>
                    <td>
                      {record.is_suspicious ? (
                        <span className="badge text-amber-700 bg-amber-50">
                          <AlertTriangle className="w-3 h-3" /> Yes
                        </span>
                      ) : (
                        <span className="text-xs text-neutral-400">—</span>
                      )}
                    </td>
                    <td>
                      <div className="space-y-0.5">
                        {record.validation_errors.slice(0, 2).map((e) => (
                          <p key={e.id} className="text-xs text-danger-600">
                            [{e.error_code}] {e.field_name}: {e.message.slice(0, 60)}
                          </p>
                        ))}
                        {record.suspicion_reasons.slice(0, 1).map((r, i) => (
                          <p key={i} className="text-xs text-amber-600">{r.slice(0, 80)}</p>
                        ))}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {records && (
            <Pagination
              page={records.page}
              numPages={records.num_pages}
              count={records.count}
              pageSize={records.page_size}
              onPageChange={setRecordPage}
            />
          )}
        </div>
      </div>
    </div>
  );
}
