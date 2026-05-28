import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { AlertTriangle } from 'lucide-react';
import { uploadsService } from '@/services/uploads';
import { PageLoading } from '@/components/common/LoadingSpinner';
import { ErrorAlert } from '@/components/common/ErrorAlert';
import { ValidationBadge } from '@/components/common/Badge';
import { Pagination } from '@/components/common/Pagination';
import { EmptyState } from '@/components/common/EmptyState';
import { formatRelativeTime } from '@/utils/formatters';
import { extractErrorMessage } from '@/services/api';

export function SuspiciousRecordsPage() {
  const [page, setPage] = useState(1);

  const { data, isLoading, error } = useQuery({
    queryKey: ['suspicious-records', page],
    queryFn: () => uploadsService.listSuspiciousRecords({ page }),
  });

  if (isLoading) return <PageLoading />;
  if (error) return <ErrorAlert message={extractErrorMessage(error)} />;

  const records = data?.results ?? [];

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-bold text-neutral-900">Suspicious Records</h1>
        <p className="text-sm text-neutral-500 mt-0.5">
          Automatically flagged anomalies requiring analyst attention
        </p>
      </div>

      <div className="card">
        {records.length === 0 ? (
          <EmptyState
            icon={AlertTriangle}
            title="No suspicious records"
            description="No anomalies have been detected in your ingested data."
          />
        ) : (
          <>
            <div className="table-container rounded-none border-none">
              <table className="table">
                <thead>
                  <tr>
                    <th>Row</th>
                    <th>Validation</th>
                    <th>Anomaly Reasons</th>
                    <th>Detected</th>
                  </tr>
                </thead>
                <tbody>
                  {records.map((record) => (
                    <tr key={record.id}>
                      <td className="font-mono text-xs text-neutral-600">Row {record.row_number}</td>
                      <td><ValidationBadge status={record.validation_status} /></td>
                      <td>
                        <div className="space-y-1 max-w-lg">
                          {record.suspicion_reasons.map((reason, i) => (
                            <div key={i} className="flex items-start gap-2">
                              <AlertTriangle className="w-3.5 h-3.5 text-amber-500 shrink-0 mt-0.5" />
                              <p className="text-xs text-neutral-700">{reason}</p>
                            </div>
                          ))}
                        </div>
                      </td>
                      <td className="text-sm text-neutral-500">
                        {formatRelativeTime(record.created_at)}
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
