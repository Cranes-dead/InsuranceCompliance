import { ComplianceStatus } from '@/lib/types';

interface StatusBadgeProps {
  status: ComplianceStatus;
  className?: string;
}

export default function StatusBadge({ status, className = '' }: StatusBadgeProps) {
  const getStatusConfig = () => {
    switch (status) {
      case 'COMPLIANT':
        return {
          bg: 'bg-green-100',
          text: 'text-green-800',
          icon: '✓',
          label: 'Compliant'
        };
      case 'NON_COMPLIANT':
        return {
          bg: 'bg-red-100',
          text: 'text-red-800',
          icon: '✗',
          label: 'Non-Compliant'
        };
      case 'REQUIRES_REVIEW':
        return {
          bg: 'bg-yellow-100',
          text: 'text-yellow-800',
          icon: '⚠',
          label: 'Requires Review'
        };
    }
  };

  const config = getStatusConfig();

  return (
    <div
      className={`inline-flex items-center gap-2 px-4 py-2 rounded-full font-semibold ${config.bg} ${config.text} ${className}`}
    >
      <span className="text-lg">{config.icon}</span>
      <span>{config.label}</span>
    </div>
  );
}
