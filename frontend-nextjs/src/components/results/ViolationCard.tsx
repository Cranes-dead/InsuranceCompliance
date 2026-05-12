import { Violation } from '@/lib/types';
import { AlertTriangle, AlertCircle, Info } from 'lucide-react';
import { Card } from '@/components/ui/card';

interface ViolationCardProps {
  violation: Violation;
}

export default function ViolationCard({ violation }: ViolationCardProps) {
  const getSeverityConfig = () => {
    switch (violation.severity) {
      case 'CRITICAL':
      case 'HIGH':
        return {
          border: 'border-rose-500/20 dark:border-rose-500/30 group-hover:border-rose-500/50',
          bg: 'bg-rose-500/5 dark:bg-rose-500/10 hover:bg-rose-500/10',
          glow: 'bg-rose-500',
          icon: AlertCircle,
          badgeText: 'text-rose-500 dark:text-rose-400',
          badgeBg: 'bg-rose-500/10 dark:bg-rose-500/20',
          badgeBorder: 'border-rose-500/20 dark:border-rose-500/30',
        };
      case 'MEDIUM':
        return {
          border: 'border-amber-500/20 dark:border-amber-500/30 group-hover:border-amber-500/50',
          bg: 'bg-amber-500/5 dark:bg-amber-500/10 hover:bg-amber-500/10',
          glow: 'bg-amber-500',
          icon: AlertTriangle,
          badgeText: 'text-amber-500 dark:text-amber-400',
          badgeBg: 'bg-amber-500/10 dark:bg-amber-500/20',
          badgeBorder: 'border-amber-500/20 dark:border-amber-500/30',
        };
      case 'LOW':
        return {
          border: 'border-chart-1/20 dark:border-chart-1/30 group-hover:border-chart-1/50',
          bg: 'bg-chart-1/5 dark:bg-chart-1/10 hover:bg-chart-1/10',
          glow: 'bg-chart-1',
          icon: Info,
          badgeText: 'text-chart-1',
          badgeBg: 'bg-chart-1/10 dark:bg-chart-1/20',
          badgeBorder: 'border-chart-1/20 dark:border-chart-1/30',
        };
      default:
        return {
          border: 'border-border group-hover:border-muted-foreground/30',
          bg: 'bg-muted/10 hover:bg-muted/20',
          glow: 'bg-muted',
          icon: Info,
          badgeText: 'text-muted-foreground',
          badgeBg: 'bg-muted/20',
          badgeBorder: 'border-border',
        };
    }
  };

  const config = getSeverityConfig();
  const Icon = config.icon;

  return (
    <Card className={`group relative overflow-hidden p-5 transition-all duration-500 backdrop-blur-sm ${config.border} ${config.bg}`}>
      {/* Ambient glow */}
      <div className={`absolute -right-16 -top-16 size-32 rounded-full blur-[48px] opacity-0 group-hover:opacity-10 transition-opacity duration-700 pointer-events-none ${config.glow}`} />

      <div className="flex items-start gap-4 relative z-10">
        <div className={`size-10 rounded-xl flex items-center justify-center border flex-shrink-0 shadow-inner group-hover:scale-105 transition-transform duration-500 ${config.badgeBg} ${config.badgeBorder}`}>
          <Icon className={`size-5 ${config.badgeText}`} />
        </div>
        
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between gap-2 mb-3">
            <h4 className="text-base font-medium text-foreground font-sans truncate">{violation.regulation_reference}</h4>
            <div className={`px-2.5 py-1 rounded-full text-[10px] font-semibold uppercase tracking-wider border flex-shrink-0 ${config.badgeBg} ${config.badgeText} ${config.badgeBorder}`}>
              {violation.severity}
            </div>
          </div>
          
          <div className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-md bg-background/50 border border-border/50 text-xs text-muted-foreground mb-3">
            <span className="font-medium">Type:</span> {violation.type}
          </div>
          
          <p className="text-sm text-foreground/80 mb-3 leading-relaxed">{violation.description}</p>
          
          {violation.recommendation && (
            <div className="mt-4 p-3.5 bg-background/60 rounded-xl border border-border/50 backdrop-blur-md">
              <p className="text-xs text-muted-foreground leading-relaxed">
                <span className="font-semibold text-foreground mr-1.5 uppercase tracking-wider text-[10px]">Recommendation</span>
                <br className="mb-1" />
                {violation.recommendation}
              </p>
            </div>
          )}
        </div>
      </div>
    </Card>
  );
}
