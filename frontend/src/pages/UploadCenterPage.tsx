import { useRef, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { CheckCircle, CloudUpload, FileText, Upload, X } from 'lucide-react';
import { Link } from 'react-router-dom';
import { uploadsService } from '@/services/uploads';
import { extractErrorMessage } from '@/services/api';
import { PageLoading } from '@/components/common/LoadingSpinner';
import { ErrorAlert } from '@/components/common/ErrorAlert';
import type { DataSource } from '@/types';

export function UploadCenterPage() {
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [selectedSource, setSelectedSource] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [notes, setNotes] = useState('');
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadedSession, setUploadedSession] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const { data: sourcesData, isLoading } = useQuery({
    queryKey: ['data-sources'],
    queryFn: () => uploadsService.listDataSources(),
  });

  const uploadMutation = useMutation({
    mutationFn: ({ sourceId, file, notes }: { sourceId: string; file: File; notes: string }) =>
      uploadsService.uploadFile(sourceId, file, notes, setUploadProgress),
    onSuccess: (session) => {
      setUploadedSession(session.id);
      queryClient.invalidateQueries({ queryKey: ['upload-sessions'] });
      setSelectedFile(null);
      setSelectedSource('');
      setNotes('');
      setUploadProgress(0);
    },
    onError: (err) => {
      setError(extractErrorMessage(err));
      setUploadProgress(0);
    },
  });

  const handleFileDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file) setSelectedFile(file);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedSource || !selectedFile) return;
    setError(null);
    setUploadedSession(null);
    uploadMutation.mutate({ sourceId: selectedSource, file: selectedFile, notes });
  };

  if (isLoading) return <PageLoading />;

  const sources: DataSource[] = sourcesData?.results ?? [];

  const SOURCE_TYPE_DESCRIPTIONS: Record<string, string> = {
    SAP_FUEL: 'SAP fuel & procurement CSV exports (invoice-level fuel data)',
    UTILITY_ELECTRICITY: 'Utility electricity billing data (meter-level consumption)',
    CORPORATE_TRAVEL: 'Corporate travel records (flights, hotels, transport)',
  };

  return (
    <div className="max-w-2xl space-y-6">
      <div>
        <h1 className="text-xl font-bold text-neutral-900">Upload Center</h1>
        <p className="text-sm text-neutral-500 mt-0.5">
          Ingest ESG data files for validation, normalization, and emissions calculation.
        </p>
      </div>

      {error && <ErrorAlert message={error} dismissible />}

      {uploadedSession && (
        <div className="flex items-start gap-3 p-4 rounded-md bg-success-50 border border-success-100 text-success-700">
          <CheckCircle className="w-5 h-5 shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-medium">Upload queued for processing.</p>
            <p className="text-sm mt-0.5">
              The file is being ingested in the background.{' '}
              <Link to={`/uploads/${uploadedSession}`} className="underline font-medium">
                View status →
              </Link>
            </p>
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit} className="card p-6 space-y-5">
        {/* Data Source */}
        <div>
          <label className="label">Data Source</label>
          <select
            className="input"
            value={selectedSource}
            onChange={(e) => setSelectedSource(e.target.value)}
            required
          >
            <option value="">Select a data source…</option>
            {sources.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </select>
          {selectedSource && sources.find((s) => s.id === selectedSource) && (
            <p className="text-xs text-neutral-500 mt-1.5">
              {SOURCE_TYPE_DESCRIPTIONS[sources.find((s) => s.id === selectedSource)!.source_type] ?? ''}
            </p>
          )}
        </div>

        {/* File Drop */}
        <div>
          <label className="label">CSV File</label>
          <div
            onDragOver={(e) => e.preventDefault()}
            onDrop={handleFileDrop}
            onClick={() => fileInputRef.current?.click()}
            className="border-2 border-dashed border-neutral-200 rounded-lg p-8 text-center cursor-pointer hover:border-brand-400 hover:bg-brand-50/30 transition-colors"
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv,.xlsx,.xls"
              className="sr-only"
              onChange={(e) => setSelectedFile(e.target.files?.[0] ?? null)}
            />
            {selectedFile ? (
              <div className="flex items-center justify-center gap-3">
                <FileText className="w-6 h-6 text-brand-500" />
                <div className="text-left">
                  <p className="text-sm font-medium text-neutral-800">{selectedFile.name}</p>
                  <p className="text-xs text-neutral-500">
                    {(selectedFile.size / 1024).toFixed(0)} KB
                  </p>
                </div>
                <button
                  type="button"
                  onClick={(e) => { e.stopPropagation(); setSelectedFile(null); }}
                  className="ml-2 text-neutral-400 hover:text-neutral-600"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <>
                <CloudUpload className="w-8 h-8 text-neutral-300 mx-auto mb-2" />
                <p className="text-sm text-neutral-600 font-medium">Drop file here or click to browse</p>
                <p className="text-xs text-neutral-400 mt-1">CSV, XLSX — max 100 MB</p>
              </>
            )}
          </div>
        </div>

        {/* Notes */}
        <div>
          <label className="label">
            Notes <span className="text-neutral-400 font-normal">(optional)</span>
          </label>
          <textarea
            className="input resize-none h-20"
            placeholder="e.g. Q1 2024 fuel procurement export from SAP S/4HANA…"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
          />
        </div>

        {/* Progress */}
        {uploadMutation.isPending && uploadProgress > 0 && (
          <div>
            <div className="flex justify-between text-xs text-neutral-600 mb-1">
              <span>Uploading…</span>
              <span>{uploadProgress}%</span>
            </div>
            <div className="h-2 bg-neutral-100 rounded-full overflow-hidden">
              <div
                className="h-full bg-brand-500 rounded-full transition-all"
                style={{ width: `${uploadProgress}%` }}
              />
            </div>
          </div>
        )}

        <button
          type="submit"
          className="btn-primary w-full"
          disabled={!selectedSource || !selectedFile || uploadMutation.isPending}
        >
          <Upload className="w-4 h-4" />
          {uploadMutation.isPending ? 'Uploading…' : 'Upload & Process'}
        </button>
      </form>

      {/* Supported formats */}
      <div className="card p-5">
        <h2 className="text-sm font-semibold text-neutral-700 mb-3">Supported Data Sources</h2>
        <div className="space-y-2">
          {[
            { type: 'SAP Fuel & Procurement', desc: 'Invoice-level fuel data with vendor, quantity, units, date. Supports German column names.' },
            { type: 'Utility Electricity', desc: 'Meter-level billing data with kWh/MWh consumption, billing periods, and tariff categories.' },
            { type: 'Corporate Travel', desc: 'Trip-level data with IATA airport codes, travel class, hotel nights, and transport mode.' },
          ].map(({ type, desc }) => (
            <div key={type} className="flex gap-3">
              <FileText className="w-4 h-4 text-brand-400 shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-medium text-neutral-700">{type}</p>
                <p className="text-xs text-neutral-500">{desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
