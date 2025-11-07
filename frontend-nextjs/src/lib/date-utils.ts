/**
 * Utility functions for date and time formatting
 */

/**
 * Format timestamp with timezone indicator
 * @param timestamp ISO string timestamp
 * @param includeTime Whether to include time (default: false for dates only)
 * @returns Formatted date string with timezone
 */
export function formatTimestamp(timestamp: string, includeTime: boolean = false): string {
  const date = new Date(timestamp);
  
  if (includeTime) {
    return date.toLocaleString() + ' UTC';
  }
  
  return date.toLocaleDateString() + ' UTC';
}

/**
 * Format relative time (e.g., "2 hours ago")
 * @param timestamp ISO string timestamp
 * @returns Relative time string
 */
export function formatRelativeTime(timestamp: string): string {
  const date = new Date(timestamp);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffSec = Math.floor(diffMs / 1000);
  const diffMin = Math.floor(diffSec / 60);
  const diffHour = Math.floor(diffMin / 60);
  const diffDay = Math.floor(diffHour / 24);

  if (diffSec < 60) {
    return 'Just now';
  } else if (diffMin < 60) {
    return `${diffMin} minute${diffMin > 1 ? 's' : ''} ago`;
  } else if (diffHour < 24) {
    return `${diffHour} hour${diffHour > 1 ? 's' : ''} ago`;
  } else if (diffDay < 7) {
    return `${diffDay} day${diffDay > 1 ? 's' : ''} ago`;
  } else {
    return formatTimestamp(timestamp);
  }
}
