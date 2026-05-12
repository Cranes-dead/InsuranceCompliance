import { ComplianceStatus } from '@/lib/types';
import { Badge } from '@/components/ui/badge';
import { CheckCircle, XCircle, AlertTriangle } from 'lucide-react';

interface StatusBadgeProps {
  status: ComplianceStatus;
  className?: string;
}

export default function StatusBadge({ status, className = '' }: StatusBadgeProps) {
  const getStatusConfig = () => {
    switch (status) {
      case 'COMPLIANT':
        return {
          variant: 'default' as const,
          icon: CheckCircle,
          label: 'Compliant',
          className: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-400 border-emerald-200 dark:border-emerald-800',
        };
      case 'NON_COMPLIANT':
        return {
          variant: 'destructive' as const,
          icon: XCircle,
          label: 'Non-Compliant',
          className: '',
        };
      case 'REQUIRES_REVIEW':
        return {
          variant: 'secondary' as const,
          icon: AlertTriangle,
          label: 'Requires Review',
          className: 'bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-400 border-amber-200 dark:border-amber-800',
        };
    }
  };

  const config = getStatusConfig();
  const Icon = config.icon;

  return (
    <Badge variant="outline" className={`gap-1.5 px-3 py-1 text-xs ${config.className} ${className}`}>
      <Icon className="size-3" />
      {config.label}
    </Badge>
  );
}
