import { useQuery } from '@tanstack/react-query';
import { AlertTriangle, ClipboardList, TrendingUp, Zap } from 'lucide-react';
import { Link } from 'react-router-dom';
import { analyticsService } from '@/services/analytics';
import { PageLoading } from '@/components/common/LoadingSpinner';
import { ErrorAlert } from '@/components/common/ErrorAlert';
import { StatusBadge } from '@/components/common/Badge';
import { formatCO2e, formatNumber, formatRelativeTime } from '@/utils/formatters';
import { extractErrorMessage } from '@/services/api';

function StatCard({
  label,
  value,
  sublabel,
  icon: Icon,
  iconColor,
}: {
  label: string;
  value: string;
  sublabel?: string;
  icon: React.ElementType;
  iconColor: string;
}) {
  return (
    <div className="card p-5">
      <div className="flex items-center justify-between mb-3">
        <p className="text-xs font-medium text-neutral-500 uppercase tracking-wide">{label}</p>
        <div className={`w-8 h-8 rounded-md flex items-center justify-center ${iconColor}`}>
          <Icon className="w-4 h-4" />
        </div>
      </div>
      <p className="text-2xl font-bold text-neutral-900">{value}</p>
      {sublabel && <p className="text-xs text-neutral-500 mt-1">{sublabel}</p>}
    </div>
  );
}

export function DashboardPage() {
  const { data: overview, isLoading, error } = useQuery({
    queryKey: ['analytics', 'overview'],
    queryFn: () => analyticsService.getOverview(),
  });

  if (isLoading) return <PageLoading />;
  if (error) return <ErrorAlert message={extractErrorMessage(error)} />;
  if (!overview) return null;

  const scopeBreakdown = overview.scope_breakdown_kg ?? {};

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold text-neutral-900">Dashboard</h1>
        <p className="text-sm text-neutral-500 mt-0.5">ESG data overview for your organization</p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Total CO₂e (Approved)"
          value={formatCO2e(overview.total_co2e_kg)}
          sublabel={`${formatNumber(overview.total_co2e_mt, 2)} metric tons`}
          icon={Zap}
          iconColor="bg-brand-50 text-brand-600"
        />
        <StatCard
          label="Pending Review"
          value={formatNumber(overview.pending_review_count)}
          sublabel="records awaiting analyst"
          icon={ClipboardList}
          iconColor="bg-amber-50 text-amber-600"
        />
        <StatCard
          label="Suspicious Records"
          value={formatNumber(overview.suspicious_record_count)}
          sublabel="anomalies flagged"
          icon={AlertTriangle}
          iconColor="bg-danger-50 text-danger-600"
        />
        <StatCard
          label="Validation Failures"
          value={formatNumber(overview.failed_validation_count)}
          sublabel="rows failed validation"
          icon={TrendingUp}
          iconColor="bg-neutral-100 text-neutral-500"
        />
      </div>

      {/* Scope Breakdown */}
      <div className="card p-5">
        <h2 className="text-sm font-semibold text-neutral-700 mb-4">Emissions by Scope (Approved)</h2>
        <div className="space-y-3">
          {[
            { key: 'SCOPE_1', label: 'Scope 1 — Direct Emissions', color: 'bg-orange-500' },
            { key: 'SCOPE_2', label: 'Scope 2 — Purchased Energy', color: 'bg-blue-500' },
            { key: 'SCOPE_3', label: 'Scope 3 — Value Chain', color: 'bg-purple-500' },
          ].map(({ key, label, color }) => {
            const val = scopeBreakdown[key as keyof typeof scopeBreakdown] ?? 0;
            const total = overview.total_co2e_kg || 1;
            const pct = Math.round((val / total) * 100);
            return (
              <div key={key}>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs text-neutral-600">{label}</span>
                  <span className="text-xs font-medium text-neutral-800">{formatCO2e(val)}</span>
                </div>
                <div className="h-2 bg-neutral-100 rounded-full overflow-hidden">
                  <div className={`h-full ${color} rounded-full`} style={{ width: `${pct}%` }} />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Recent Uploads */}
      <div className="card">
        <div className="flex items-center justify-between px-5 py-4 border-b border-neutral-100">
          <h2 className="text-sm font-semibold text-neutral-700">Recent Uploads</h2>
          <Link to="/uploads/history" className="text-xs text-brand-600 hover:underline">
            View all
          </Link>
        </div>
        <div className="divide-y divide-neutral-100">
          {overview.recent_uploads.length === 0 ? (
            <p className="px-5 py-6 text-sm text-neutral-500 text-center">No uploads yet.</p>
          ) : (
            overview.recent_uploads.map((upload) => (
              <Link
                key={upload.id}
                to={`/uploads/${upload.id}`}
                className="flex items-center justify-between px-5 py-3 hover:bg-neutral-50 transition-colors"
              >
                <div className="min-w-0">
                  <p className="text-sm font-medium text-neutral-800 truncate">{upload.original_filename}</p>
                  <p className="text-xs text-neutral-500 mt-0.5">
                    {formatNumber(upload.total_rows)} rows · {formatRelativeTime(upload.created_at)}
                  </p>
                </div>
                <StatusBadge status={upload.status} />
              </Link>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
