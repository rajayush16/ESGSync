import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { CheckCircle, XCircle } from 'lucide-react';
import { reviewsService } from '@/services/reviews';
import { PageLoading } from '@/components/common/LoadingSpinner';
import { ErrorAlert } from '@/components/common/ErrorAlert';
import { DecisionBadge, ScopeBadge } from '@/components/common/Badge';
import { Pagination } from '@/components/common/Pagination';
import { EmptyState } from '@/components/common/EmptyState';
import { ConfirmDialog } from '@/components/common/ConfirmDialog';
import { formatCO2e, formatRelativeTime } from '@/utils/formatters';
import { extractErrorMessage } from '@/services/api';
import type { ReviewTask } from '@/types';
import { ClipboardList } from 'lucide-react';

export function ReviewQueuePage() {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [decisionFilter, setDecisionFilter] = useState('PENDING');
  const [selectedTask, setSelectedTask] = useState<ReviewTask | null>(null);
  const [dialogAction, setDialogAction] = useState<'approve' | 'reject' | null>(null);
  const [rejectReason, setRejectReason] = useState('');
  const [actionError, setActionError] = useState<string | null>(null);

  const { data, isLoading, error } = useQuery({
    queryKey: ['review-tasks', page, decisionFilter],
    queryFn: () =>
      reviewsService.list({ page, decision: decisionFilter || undefined }),
  });

  const approveMutation = useMutation({
    mutationFn: (taskId: string) => reviewsService.approve(taskId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['review-tasks'] });
      queryClient.invalidateQueries({ queryKey: ['analytics'] });
      setSelectedTask(null);
      setDialogAction(null);
    },
    onError: (err) => setActionError(extractErrorMessage(err)),
  });

  const rejectMutation = useMutation({
    mutationFn: ({ taskId, reason }: { taskId: string; reason: string }) =>
      reviewsService.reject(taskId, reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['review-tasks'] });
      setSelectedTask(null);
      setDialogAction(null);
      setRejectReason('');
    },
    onError: (err) => setActionError(extractErrorMessage(err)),
  });

  if (isLoading) return <PageLoading />;
  if (error) return <ErrorAlert message={extractErrorMessage(error)} />;

  const tasks = data?.results ?? [];

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-bold text-neutral-900">Review Queue</h1>
        <p className="text-sm text-neutral-500 mt-0.5">Analyst review and approval workflow</p>
      </div>

      {actionError && <ErrorAlert message={actionError} dismissible />}

      {/* Filters */}
      <div className="flex gap-2">
        {['PENDING', 'APPROVED', 'REJECTED', 'ESCALATED', ''].map((d) => (
          <button
            key={d}
            onClick={() => { setDecisionFilter(d); setPage(1); }}
            className={decisionFilter === d ? 'btn-primary text-xs' : 'btn-secondary text-xs'}
          >
            {d || 'All'}
          </button>
        ))}
      </div>

      <div className="card">
        {tasks.length === 0 ? (
          <EmptyState
            icon={ClipboardList}
            title="No review tasks"
            description={decisionFilter === 'PENDING' ? 'All caught up! No pending reviews.' : 'No tasks match this filter.'}
          />
        ) : (
          <>
            <div className="table-container rounded-none border-none">
              <table className="table">
                <thead>
                  <tr>
                    <th>Emission Record</th>
                    <th>Scope</th>
                    <th>CO₂e</th>
                    <th>Decision</th>
                    <th>Assigned</th>
                    <th>Created</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {tasks.map((task) => {
                    const rec = task.emission_record_detail;
                    return (
                      <tr key={task.id}>
                        <td>
                          <p className="text-sm font-medium text-neutral-800 font-mono text-xs">
                            {rec?.upload_session_filename ?? '—'}
                          </p>
                          <p className="text-xs text-neutral-400">{rec?.category_display}</p>
                        </td>
                        <td>{rec && <ScopeBadge scope={rec.scope} />}</td>
                        <td className="font-mono text-sm">{formatCO2e(rec?.co2e_kg)}</td>
                        <td><DecisionBadge decision={task.decision} /></td>
                        <td className="text-sm">{task.assigned_to_name ?? <span className="text-neutral-400">—</span>}</td>
                        <td className="text-sm text-neutral-500">{formatRelativeTime(task.created_at)}</td>
                        <td>
                          {task.decision === 'PENDING' && (
                            <div className="flex gap-1.5">
                              <button
                                onClick={() => { setSelectedTask(task); setDialogAction('approve'); }}
                                className="p-1.5 rounded text-success-600 hover:bg-success-50"
                                title="Approve"
                              >
                                <CheckCircle className="w-4 h-4" />
                              </button>
                              <button
                                onClick={() => { setSelectedTask(task); setDialogAction('reject'); }}
                                className="p-1.5 rounded text-danger-600 hover:bg-danger-50"
                                title="Reject"
                              >
                                <XCircle className="w-4 h-4" />
                              </button>
                            </div>
                          )}
                        </td>
                      </tr>
                    );
                  })}
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

      {/* Approve Confirm */}
      <ConfirmDialog
        isOpen={dialogAction === 'approve' && !!selectedTask}
        title="Approve Record"
        description="Approve this emission record? It will move to APPROVED status and count toward your totals."
        confirmLabel="Approve"
        onConfirm={() => void approveMutation.mutateAsync(selectedTask!.id)}
        onCancel={() => { setSelectedTask(null); setDialogAction(null); }}
      />

      {/* Reject Dialog */}
      {dialogAction === 'reject' && selectedTask && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-md p-6 mx-4">
            <h3 className="text-base font-semibold text-neutral-900 mb-3">Reject Record</h3>
            <p className="text-sm text-neutral-600 mb-4">
              Please provide a reason for rejection. This will be recorded in the audit log.
            </p>
            <textarea
              className="input resize-none h-24"
              placeholder="Rejection reason…"
              value={rejectReason}
              onChange={(e) => setRejectReason(e.target.value)}
            />
            <div className="flex justify-end gap-3 mt-4">
              <button
                className="btn-secondary"
                onClick={() => { setSelectedTask(null); setDialogAction(null); setRejectReason(''); }}
              >
                Cancel
              </button>
              <button
                className="btn-danger"
                disabled={!rejectReason.trim() || rejectMutation.isPending}
                onClick={() => rejectMutation.mutate({ taskId: selectedTask.id, reason: rejectReason })}
              >
                {rejectMutation.isPending ? 'Rejecting…' : 'Reject'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
