import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(date: string) {
  return new Date(date).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

export function getStatusColor(status: string) {
  switch (status) {
    case 'COMPLIANT':
      return 'text-green-600 bg-green-100';
    case 'NON_COMPLIANT':
      return 'text-red-600 bg-red-100';
    case 'REQUIRES_REVIEW':
      return 'text-yellow-600 bg-yellow-100';
    default:
      return 'text-gray-600 bg-gray-100';
  }
}

export function getSeverityColor(severity: string) {
  switch (severity) {
    case 'CRITICAL':
      return 'text-red-700 bg-red-100';
    case 'HIGH':
      return 'text-orange-700 bg-orange-100';
    case 'MEDIUM':
      return 'text-yellow-700 bg-yellow-100';
    case 'LOW':
      return 'text-blue-700 bg-blue-100';
    default:
      return 'text-gray-700 bg-gray-100';
  }
}
