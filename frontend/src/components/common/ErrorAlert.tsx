import { AlertTriangle, X } from 'lucide-react';
import { useState } from 'react';

interface ErrorAlertProps {
  title?: string;
  message: string;
  dismissible?: boolean;
}

export function ErrorAlert({ title = 'Error', message, dismissible = false }: ErrorAlertProps) {
  const [visible, setVisible] = useState(true);
  if (!visible) return null;

  return (
    <div className="flex items-start gap-3 p-4 rounded-md bg-danger-50 border border-danger-200 text-danger-700">
      <AlertTriangle className="w-5 h-5 shrink-0 mt-0.5" />
      <div className="flex-1 min-w-0">
        <p className="font-medium text-sm">{title}</p>
        <p className="text-sm mt-0.5 text-danger-600">{message}</p>
      </div>
      {dismissible && (
        <button onClick={() => setVisible(false)} className="text-danger-400 hover:text-danger-600">
          <X className="w-4 h-4" />
        </button>
      )}
    </div>
  );
}
