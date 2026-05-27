import React from 'react';

interface AnomalyBadgeProps {
  code: string;
}

const codeStyleMap: Record<string, string> = {
  DUPLICATE_PERIOD: 'badge badge-danger',
  NEGATIVE_VALUE:   'badge badge-danger',
  ZERO_VALUE:       'badge badge-warning',
  FUTURE_DATE:      'badge badge-warning',
  UNKNOWN_FACILITY: 'badge badge-warning',
  UNIT_UNCERTAINTY: 'badge badge-warning',
  DISTANCE_INFERRED:    'badge badge-info',
  BILLING_PERIOD_SPLIT: 'badge badge-info',
};

export const AnomalyBadge: React.FC<AnomalyBadgeProps> = ({ code }) => {
  const cls = codeStyleMap[code] || 'badge badge-neutral';
  return <span className={cls}>{code.replace(/_/g, ' ')}</span>;
};
