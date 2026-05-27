import React from 'react';

interface ScopeBadgeProps {
  scope: 'SCOPE_1' | 'SCOPE_2' | 'SCOPE_3';
}

const scopeMap: Record<string, { className: string; label: string }> = {
  SCOPE_1: { className: 'badge badge-scope1', label: 'Scope 1 (Direct)' },
  SCOPE_2: { className: 'badge badge-scope2', label: 'Scope 2 (Indirect)' },
  SCOPE_3: { className: 'badge badge-scope3', label: 'Scope 3 (Value Chain)' },
};

export const ScopeBadge: React.FC<ScopeBadgeProps> = ({ scope }) => {
  const config = scopeMap[scope] || { className: 'badge badge-neutral', label: scope };
  return <span className={config.className}>{config.label}</span>;
};
