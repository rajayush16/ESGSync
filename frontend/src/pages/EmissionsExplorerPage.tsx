import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Zap } from 'lucide-react';
import { Link } from 'react-router-dom';
import { emissionsService } from '@/services/emissions';
import { PageLoading } from '@/components/common/LoadingSpinner';
import { ErrorAlert } from '@/components/common/ErrorAlert';
import { ScopeBadge, StatusBadge } from '@/components/common/Badge';
import { Pagination } from '@/components/common/Pagination';
import { EmptyState } from '@/components/common/EmptyState';
import { formatCO2e, formatDate, formatNumber } from '@/utils/formatters';
import { extractErrorMessage } from '@/services/api';
import type { EmissionSummary } from '@/types';

export function EmissionsExplorerPage() {
  const [page, setPage] = useState(1);
  const [scopeFilter, setScopeFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

  const { data, isLoading, error } = useQuery({
    queryKey: ['emissions', page, scopeFilter, statusFilter],
    queryFn: () =>
      emissionsService.list({
        page,
        scope: scopeFilter || undefined,
        status: statusFilter || undefined,
      }),
  });

  const { data: summary } = useQuery({
    queryKey: ['emissions-summary'],
    queryFn: () => emissionsService.getSummary(),
  });

  if (isLoading) return <PageLoading />;
  if (error) return <ErrorAlert message={extractErrorMessage(error)} />;

  const records = data?.results ?? [];

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-xl font-bold text-neutral-900">Emissions Explorer</h1>
        <p className="text-sm text-neutral-500 mt-0.5">Normalized emission records across all scopes</p>
      </div>

      {/* Scope Summary */}
      {summary && summary.length > 0 && (
        <div className="grid grid-cols-3 gap-4">
          {summary.map((s: EmissionSummary) => (
            <div key={s.scope} className="card p-4">
              <div className="flex items-center justify-between mb-2">
                <ScopeBadge scope={s.scope} />
                <span className="text-xs text-neutral-400">{formatNumber(s.record_count)} records</span>
              </div>
              <p className="text-xl font-bold text-neutral-900">{formatCO2e(s.total_co2e_kg)}</p>
              <p className="text-xs text-neutral-500 mt-0.5">{s.scope_display}</p>
            </div>
          ))}
        </div>
      )}

      {/* Filters */}
      <div className="flex gap-3">
        <select
          className="input w-40"
          value={scopeFilter}
          onChange={(e) => { setScopeFilter(e.target.value); setPage(1); }}
        >
          <option value="">All scopes</option>
          <option value="SCOPE_1">Scope 1</option>
          <option value="SCOPE_2">Scope 2</option>
          <option value="SCOPE_3">Scope 3</option>
        </select>
        <select
          className="input w-48"
          value={statusFilter}
          onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
        >
          <option value="">All statuses</option>
          <option value="REVIEW_PENDING">Pending Review</option>
          <option value="APPROVED">Approved</option>
          <option value="REJECTED">Rejected</option>
          <option value="LOCKED_FOR_AUDIT">Locked</option>
        </select>
      </div>

      <div className="card">
        {records.length === 0 ? (
          <EmptyState
            icon={Zap}
            title="No emission records"
            description="Upload and process data files to generate emission records."
          />
        ) : (
          <>
            <div className="table-container rounded-none border-none">
              <table className="table">
                <thead>
                  <tr>
                    <th>Scope</th>
                    <th>Category</th>
                    <th>CO₂e</th>
                    <th>Status</th>
                    <th>Source</th>
                    <th>Period</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {records.map((record) => (
                    <tr key={record.id}>
                      <td><ScopeBadge scope={record.scope} /></td>
                      <td className="text-sm text-neutral-700">{record.category_display}</td>
                      <td className="font-mono text-sm font-medium">{formatCO2e(record.co2e_kg)}</td>
                      <td><StatusBadge status={record.status} /></td>
                      <td className="text-sm text-neutral-500 max-w-xs truncate">
                        {record.upload_session_filename}
                      </td>
                      <td className="text-sm text-neutral-500">
                        {formatDate(record.reporting_period_start)}
                      </td>
                      <td>
                        <Link
                          to={`/emissions/${record.id}`}
                          className="text-xs text-brand-600 hover:underline"
                        >
                          Details →
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
