import { ChevronLeft, ChevronRight } from 'lucide-react';
import clsx from 'clsx';

interface PaginationProps {
  page: number;
  numPages: number;
  count: number;
  pageSize: number;
  onPageChange: (page: number) => void;
}

export function Pagination({ page, numPages, count, pageSize, onPageChange }: PaginationProps) {
  if (numPages <= 1) return null;

  const start = (page - 1) * pageSize + 1;
  const end = Math.min(page * pageSize, count);

  return (
    <div className="flex items-center justify-between px-4 py-3 border-t border-neutral-200">
      <p className="text-sm text-neutral-500">
        Showing <span className="font-medium text-neutral-700">{start}</span>–
        <span className="font-medium text-neutral-700">{end}</span> of{' '}
        <span className="font-medium text-neutral-700">{count}</span>
      </p>
      <div className="flex items-center gap-1">
        <button
          onClick={() => onPageChange(page - 1)}
          disabled={page === 1}
          className={clsx(
            'p-1.5 rounded-md text-neutral-500 hover:bg-neutral-100 disabled:opacity-40 disabled:cursor-not-allowed',
          )}
        >
          <ChevronLeft className="w-4 h-4" />
        </button>
        {Array.from({ length: numPages }, (_, i) => i + 1)
          .filter((p) => Math.abs(p - page) <= 2 || p === 1 || p === numPages)
          .reduce<(number | '...')[]>((acc, p, idx, arr) => {
            if (idx > 0 && p - (arr[idx - 1] as number) > 1) acc.push('...');
            acc.push(p);
            return acc;
          }, [])
          .map((p, idx) =>
            p === '...' ? (
              <span key={`ellipsis-${idx}`} className="px-2 text-neutral-400 text-sm">…</span>
            ) : (
              <button
                key={p}
                onClick={() => onPageChange(p as number)}
                className={clsx(
                  'min-w-[32px] px-2 py-1 rounded-md text-sm font-medium',
                  p === page
                    ? 'bg-brand-600 text-white'
                    : 'text-neutral-600 hover:bg-neutral-100',
                )}
              >
                {p}
              </button>
            ),
          )}
        <button
          onClick={() => onPageChange(page + 1)}
          disabled={page === numPages}
          className="p-1.5 rounded-md text-neutral-500 hover:bg-neutral-100 disabled:opacity-40 disabled:cursor-not-allowed"
        >
          <ChevronRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
