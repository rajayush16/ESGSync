import { useState } from 'react';
import { BarChart3 } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { extractErrorMessage } from '@/services/api';

export function LoginPage() {
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await login(email, password);
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-neutral-50 flex flex-col justify-center">
      <div className="w-full max-w-sm mx-auto px-4">
        {/* Logo */}
        <div className="flex flex-col items-center mb-8">
          <div className="w-12 h-12 rounded-xl bg-brand-600 flex items-center justify-center mb-4 shadow-sm">
            <BarChart3 className="w-6 h-6 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-neutral-900">ESGSync</h1>
          <p className="text-sm text-neutral-500 mt-1">Enterprise ESG Data Platform</p>
        </div>

        {/* Form */}
        <div className="card p-6">
          <h2 className="text-base font-semibold text-neutral-800 mb-5">Sign in to your account</h2>

          {error && (
            <div className="mb-4 p-3 rounded-md bg-danger-50 border border-danger-200 text-danger-700 text-sm">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="email" className="label">Email address</label>
              <input
                id="email"
                type="email"
                className="input"
                placeholder="analyst@acme.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                autoComplete="email"
              />
            </div>
            <div>
              <label htmlFor="password" className="label">Password</label>
              <input
                id="password"
                type="password"
                className="input"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                autoComplete="current-password"
              />
            </div>
            <button
              type="submit"
              className="btn-primary w-full"
              disabled={loading}
            >
              {loading ? 'Signing in…' : 'Sign in'}
            </button>
          </form>
        </div>

        <p className="text-xs text-neutral-400 text-center mt-6">
          ESGSync v1.0 — Sustainability & Emissions Platform
        </p>
      </div>
    </div>
  );
}
