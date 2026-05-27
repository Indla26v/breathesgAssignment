import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../../stores/authStore';
import { logout as apiLogout } from '../../api/auth';
import { LayoutDashboard, UploadCloud, LogOut, Activity } from 'lucide-react';

export const Sidebar: React.FC = () => {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();

  const handleLogout = async () => {
    try {
      await apiLogout();
    } catch (e) {
      // ignore
    }
    logout();
    navigate('/login');
  };

  const getRoleBadge = (role?: string) => {
    switch (role) {
      case 'PLATFORM_ADMIN': return { className: 'badge badge-purple', label: 'Platform Admin' };
      case 'TENANT_ADMIN':   return { className: 'badge badge-warning', label: 'Tenant Admin' };
      default:               return { className: 'badge badge-success', label: 'Analyst' };
    }
  };

  const roleBadge = user ? getRoleBadge(user.role) : null;

  return (
    <aside className="sidebar">
      <div>
        {/* Brand */}
        <div className="sidebar-brand">
          <div className="sidebar-brand-icon">
            <Activity size={18} />
          </div>
          <div className="sidebar-brand-text">
            <h1>Breathe ESG</h1>
            <span>Ingestor</span>
          </div>
        </div>

        {/* User card */}
        {user && (
          <div className="sidebar-user-card">
            <div className="sidebar-user-name">{user.full_name}</div>
            <div className="sidebar-user-email">{user.email}</div>
            {roleBadge && (
              <span className={roleBadge.className} style={{ marginTop: 6 }}>
                {roleBadge.label}
              </span>
            )}
            <div className="sidebar-user-tenant">
              Tenant: <strong>{user.tenant_name}</strong>
            </div>
          </div>
        )}

        {/* Nav */}
        <nav className="sidebar-nav">
          <NavLink
            to="/dashboard"
            className={({ isActive }) => `sidebar-nav-link ${isActive ? 'active' : ''}`}
          >
            <LayoutDashboard size={16} />
            Dashboard
          </NavLink>
          <NavLink
            to="/upload"
            className={({ isActive }) => `sidebar-nav-link ${isActive ? 'active' : ''}`}
          >
            <UploadCloud size={16} />
            Upload File
          </NavLink>
        </nav>
      </div>

      <button onClick={handleLogout} className="sidebar-logout">
        <LogOut size={16} />
        Logout
      </button>
    </aside>
  );
};
