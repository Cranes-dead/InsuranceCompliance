'use client';

import { Policy } from '@/lib/types';
import { useRouter } from 'next/navigation';
import { FileText, ArrowRight, Calendar, Activity } from 'lucide-react';
import { Card } from '@/components/ui/card';

interface PolicyGridProps {
  policies: Policy[];
  className?: string;
}

function getStatusConfig(score: number) {
  if (score >= 80) {
    return {
      text: 'text-emerald-500 dark:text-emerald-400',
      bg: 'bg-emerald-500/10 dark:bg-emerald-500/20',
      border: 'border-emerald-500/20 dark:border-emerald-500/30',
      glow: 'bg-emerald-500',
      label: 'Compliant'
    };
  }
  if (score >= 60) {
    return {
      text: 'text-amber-500 dark:text-amber-400',
      bg: 'bg-amber-500/10 dark:bg-amber-500/20',
      border: 'border-amber-500/20 dark:border-amber-500/30',
      glow: 'bg-amber-500',
      label: 'Review Required'
    };
  }
  return {
    text: 'text-rose-500 dark:text-rose-400',
    bg: 'bg-rose-500/10 dark:bg-rose-500/20',
    border: 'border-rose-500/20 dark:border-rose-500/30',
    glow: 'bg-rose-500',
    label: 'Non-Compliant'
  };
}

export default function PolicyGrid({ policies, className = '' }: PolicyGridProps) {
  const router = useRouter();

  if (policies.length === 0) {
    return (
      <div className="text-center py-20 px-6 rounded-2xl border border-dashed border-border/50 bg-card/30">
        <FileText className="size-12 text-muted-foreground/20 mx-auto mb-4" />
        <p className="text-sm font-medium text-foreground">No policies uploaded yet</p>
        <p className="text-xs text-muted-foreground mt-1">Upload a policy document to see it in your portfolio.</p>
      </div>
    );
  }

  return (
    <div className={`grid md:grid-cols-2 lg:grid-cols-3 gap-5 ${className}`}>
      {policies.map((policy) => {
        const config = getStatusConfig(policy.score);
        
        return (
          <Card
            key={policy.id}
            onClick={() => router.push(`/analysis/${policy.id}`)}
            className="group relative overflow-hidden border-border/40 bg-card/40 backdrop-blur-md p-6 cursor-pointer transition-all duration-500 hover:shadow-2xl hover:shadow-background/50 hover:-translate-y-1 hover:border-border/80 hover:bg-card/80"
          >
            {/* Ambient background glow on hover */}
            <div className={`absolute -right-20 -top-20 size-48 rounded-full blur-[64px] opacity-0 group-hover:opacity-15 transition-opacity duration-700 pointer-events-none ${config.glow}`} />

            {/* Header: Icon & Score */}
            <div className="flex justify-between items-start mb-6">
              <div className="flex items-center gap-3">
                <div className="size-12 rounded-xl bg-muted/40 flex items-center justify-center border border-border/50 shadow-inner group-hover:scale-105 transition-transform duration-500">
                  <FileText className="size-5 text-foreground/70 group-hover:text-foreground transition-colors" />
                </div>
                <div className={`px-2.5 py-1 rounded-full text-[10px] font-semibold uppercase tracking-wider border ${config.bg} ${config.text} ${config.border}`}>
                  {config.label}
                </div>
              </div>
              <div className="flex flex-col items-end">
                <span className="text-3xl font-heading tracking-tighter leading-none group-hover:scale-105 transition-transform origin-right">
                  {policy.score}<span className="text-lg text-muted-foreground ml-0.5">%</span>
                </span>
                <span className="text-[10px] uppercase tracking-wider text-muted-foreground font-medium mt-1">
                  Compliance
                </span>
              </div>
            </div>

            {/* Content: Title & Date */}
            <div className="space-y-1.5 mb-8">
              <h3 className="text-base font-medium text-foreground line-clamp-1 group-hover:text-primary transition-colors">
                {policy.filename}
              </h3>
              <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                <Activity className="size-3.5" />
                <span>Analyzed {new Date(policy.lastAnalyzed).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })}</span>
              </div>
            </div>

            {/* Footer */}
            <div className="flex items-center justify-between pt-4 border-t border-border/40">
              <div className="flex items-center gap-1.5 text-[11px] text-muted-foreground/80">
                <Calendar className="size-3" />
                Uploaded {new Date(policy.uploadedAt).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
              </div>
              <div className="flex items-center text-xs font-medium text-foreground opacity-0 group-hover:opacity-100 transition-all -translate-x-2 group-hover:translate-x-0 duration-300">
                View Report <ArrowRight className="size-3.5 ml-1.5" />
              </div>
            </div>
          </Card>
        );
      })}
    </div>
  );
}
