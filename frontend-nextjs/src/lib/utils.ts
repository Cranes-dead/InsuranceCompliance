import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatDate(date: string) {
  return new Date(date).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

export function getStatusVariant(status: string): "default" | "secondary" | "destructive" | "outline" {
  switch (status) {
    case 'COMPLIANT':
      return 'default';
    case 'NON_COMPLIANT':
      return 'destructive';
    case 'REQUIRES_REVIEW':
      return 'secondary';
    default:
      return 'outline';
  }
}

export function getStatusLabel(status: string): string {
  switch (status) {
    case 'COMPLIANT':
      return 'Compliant';
    case 'NON_COMPLIANT':
      return 'Non-Compliant';
    case 'REQUIRES_REVIEW':
      return 'Review Required';
    default:
      return status;
  }
}

export function getSeverityColor(severity: string) {
  switch (severity) {
    case 'CRITICAL':
      return 'text-red-700 bg-red-100 dark:text-red-400 dark:bg-red-950';
    case 'HIGH':
      return 'text-orange-700 bg-orange-100 dark:text-orange-400 dark:bg-orange-950';
    case 'MEDIUM':
      return 'text-yellow-700 bg-yellow-100 dark:text-yellow-400 dark:bg-yellow-950';
    case 'LOW':
      return 'text-blue-700 bg-blue-100 dark:text-blue-400 dark:bg-blue-950';
    default:
      return 'text-muted-foreground bg-muted';
  }
}

// Keep old function for backwards compatibility
export function getStatusColor(status: string) {
  switch (status) {
    case 'COMPLIANT':
      return 'text-emerald-700 bg-emerald-100 dark:text-emerald-400 dark:bg-emerald-950';
    case 'NON_COMPLIANT':
      return 'text-red-700 bg-red-100 dark:text-red-400 dark:bg-red-950';
    case 'REQUIRES_REVIEW':
      return 'text-amber-700 bg-amber-100 dark:text-amber-400 dark:bg-amber-950';
    default:
      return 'text-muted-foreground bg-muted';
  }
}
