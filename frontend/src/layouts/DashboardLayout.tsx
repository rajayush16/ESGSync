import { useState } from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import {
  AlertTriangle,
  BarChart3,
  ChevronDown,
  ClipboardList,
  Clock,
  FileText,
  LayoutDashboard,
  LogOut,
  Upload,
  Zap,
} from 'lucide-react';
import clsx from 'clsx';
import { useAuth } from '@/contexts/AuthContext';

const NAV_ITEMS = [
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/uploads', label: 'Upload Center', icon: Upload },
  { to: '/uploads/history', label: 'Upload History', icon: Clock },
  { to: '/reviews', label: 'Review Queue', icon: ClipboardList },
  { to: '/suspicious', label: 'Suspicious Records', icon: AlertTriangle },
  { to: '/emissions', label: 'Emissions Explorer', icon: Zap },
  { to: '/audit', label: 'Audit Timeline', icon: FileText },
];

export function DashboardLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [profileOpen, setProfileOpen] = useState(false);

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  return (
    <div className="min-h-screen flex bg-neutral-50">
      {/* Sidebar */}
      <aside className="w-60 flex-shrink-0 bg-neutral-900 flex flex-col">
        {/* Logo */}
        <div className="h-16 flex items-center px-5 border-b border-neutral-800">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-md bg-brand-500 flex items-center justify-center">
              <BarChart3 className="w-4 h-4 text-white" />
            </div>
            <span className="text-white font-semibold text-sm tracking-tight">ESGSync</span>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto">
          {NAV_ITEMS.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                clsx(
                  'flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-brand-600 text-white'
                    : 'text-neutral-400 hover:text-white hover:bg-neutral-800',
                )
              }
            >
              <Icon className="w-4 h-4 shrink-0" />
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>

        {/* User */}
        <div className="border-t border-neutral-800 p-3">
          <div className="relative">
            <button
              onClick={() => setProfileOpen((v) => !v)}
              className="w-full flex items-center gap-2.5 px-2 py-2 rounded-md hover:bg-neutral-800 transition-colors text-left"
            >
              <div className="w-7 h-7 rounded-full bg-brand-500 flex items-center justify-center text-white text-xs font-semibold shrink-0">
                {user?.full_name?.[0]?.toUpperCase() ?? 'U'}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-xs font-medium text-white truncate">{user?.full_name}</p>
                <p className="text-2xs text-neutral-400 truncate">{user?.role}</p>
              </div>
              <ChevronDown className="w-3.5 h-3.5 text-neutral-400 shrink-0" />
            </button>

            {profileOpen && (
              <div className="absolute bottom-full left-0 right-0 mb-1 bg-neutral-800 rounded-md shadow-xl border border-neutral-700 overflow-hidden">
                <button
                  onClick={handleLogout}
                  className="w-full flex items-center gap-2 px-3 py-2.5 text-sm text-neutral-300 hover:bg-neutral-700 hover:text-white transition-colors"
                >
                  <LogOut className="w-4 h-4" />
                  Sign out
                </button>
              </div>
            )}
          </div>
        </div>
      </aside>

      {/* Main */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top bar */}
        <header className="h-16 bg-white border-b border-neutral-200 flex items-center px-6 shrink-0">
          <div className="flex-1" />
          <div className="flex items-center gap-2 text-sm text-neutral-500">
            <span>{user?.organization_name}</span>
          </div>
        </header>

        {/* Content */}
        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
