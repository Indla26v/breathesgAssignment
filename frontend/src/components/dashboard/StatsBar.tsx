import React from 'react';
import { DashboardSummary } from '../../types';
import { FileStack, ClipboardCheck, AlertTriangle, Lock } from 'lucide-react';

interface StatsBarProps {
  summary?: DashboardSummary;
  isLoading: boolean;
}

export const StatsBar: React.FC<StatsBarProps> = ({ summary, isLoading }) => {
  const stats = [
    {
      label: 'Pending Batches',
      value: summary?.pending_batches ?? 0,
      icon: <FileStack size={18} />,
      iconBg: '#fef6e6',
      iconColor: '#c27d0a',
    },
    {
      label: 'Awaiting Review',
      value: summary?.records_awaiting_review ?? 0,
      icon: <ClipboardCheck size={18} />,
      iconBg: '#e8f5f1',
      iconColor: '#0d9373',
    },
    {
      label: 'Flagged Anomalies',
      value: summary?.flagged_records ?? 0,
      icon: <AlertTriangle size={18} />,
      iconBg: '#fdeaec',
      iconColor: '#dc3545',
    },
    {
      label: 'Audit Locked',
      value: summary?.locked_records ?? 0,
      icon: <Lock size={18} />,
      iconBg: '#f0ebfe',
      iconColor: '#7c3aed',
    },
  ];

  return (
    <div className="stats-grid">
      {stats.map((stat, idx) => (
        <div key={idx} className="stat-card">
          <div>
            <div className="stat-label">{stat.label}</div>
            {isLoading ? (
              <div className="stat-skeleton animate-pulse" />
            ) : (
              <div className="stat-value">{stat.value}</div>
            )}
          </div>
          <div className="stat-icon" style={{ background: stat.iconBg, color: stat.iconColor }}>
            {stat.icon}
          </div>
        </div>
      ))}
    </div>
  );
};
