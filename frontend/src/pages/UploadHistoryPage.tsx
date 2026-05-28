import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { Clock } from 'lucide-react';
import { uploadsService } from '@/services/uploads';
import { PageLoading } from '@/components/common/LoadingSpinner';
import { ErrorAlert } from '@/components/common/ErrorAlert';
import { Pagination } from '@/components/common/Pagination';
import { StatusBadge } from '@/components/common/Badge';
import { EmptyState } from '@/components/common/EmptyState';
import { formatDate, formatNumber } from '@/utils/formatters';
import { extractErrorMessage } from '@/services/api';

export function UploadHistoryPage() {
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState('');

  const { data, isLoading, error } = useQuery({
    queryKey: ['upload-sessions', page, statusFilter],
    queryFn: () => uploadsService.listSessions({ page, status: statusFilter || undefined }),
  });

  if (isLoading) return <PageLoading />;
  if (error) return <ErrorAlert message={extractErrorMessage(error)} />;

  const sessions = data?.results ?? [];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-neutral-900">Upload History</h1>
          <p className="text-sm text-neutral-500 mt-0.5">All data ingestion sessions for your organization</p>
        </div>
        <Link to="/uploads" className="btn-primary">New Upload</Link>
      </div>

      {/* Filters */}
      <div className="flex gap-3">
        <select
          className="input w-48"
          value={statusFilter}
          onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
        >
          <option value="">All statuses</option>
          <option value="UPLOADED">Uploaded</option>
          <option value="VALIDATING">Validating</option>
          <option value="NORMALIZED">Normalized</option>
          <option value="REVIEW_PENDING">Review Pending</option>
          <option value="APPROVED">Approved</option>
          <option value="REJECTED">Rejected</option>
          <option value="FAILED">Failed</option>
        </select>
      </div>

      <div className="card">
        {sessions.length === 0 ? (
          <EmptyState
            icon={Clock}
            title="No upload sessions found"
            description="Upload a CSV file to get started with data ingestion."
            action={<Link to="/uploads" className="btn-primary">Upload Data</Link>}
          />
        ) : (
          <>
            <div className="table-container rounded-none border-none">
              <table className="table">
                <thead>
                  <tr>
                    <th>File</th>
                    <th>Source</th>
                    <th>Status</th>
                    <th>Rows</th>
                    <th>Success Rate</th>
                    <th>Uploaded</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {sessions.map((session) => (
                    <tr key={session.id}>
                      <td>
                        <p className="font-medium text-neutral-800 max-w-xs truncate">
                          {session.original_filename}
                        </p>
                        <p className="text-xs text-neutral-400">{session.file_size_mb} MB</p>
                      </td>
                      <td>
                        <p className="text-sm">{session.data_source_name}</p>
                        <p className="text-xs text-neutral-400">{session.data_source_type}</p>
                      </td>
                      <td><StatusBadge status={session.status} /></td>
                      <td>
                        <span className="text-sm">{formatNumber(session.total_rows)}</span>
                        {session.failed_rows > 0 && (
                          <span className="ml-2 text-xs text-danger-600">
                            {session.failed_rows} failed
                          </span>
                        )}
                      </td>
                      <td>
                        <span className={session.success_rate >= 90 ? 'text-success-600' : session.success_rate >= 70 ? 'text-warning-600' : 'text-danger-600'}>
                          {session.success_rate}%
                        </span>
                      </td>
                      <td>
                        <p className="text-sm">{formatDate(session.created_at)}</p>
                        <p className="text-xs text-neutral-400">{session.uploaded_by_name}</p>
                      </td>
                      <td>
                        <Link
                          to={`/uploads/${session.id}`}
                          className="text-xs text-brand-600 hover:underline"
                        >
                          View →
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
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
