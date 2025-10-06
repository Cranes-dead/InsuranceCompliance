'use client';

import { Policy } from '@/lib/types';
import { useRouter } from 'next/navigation';
import { FileText, Eye } from 'lucide-react';
import { getStatusColor } from '@/lib/utils';

interface PolicyGridProps {
  policies: Policy[];
  className?: string;
}

export default function PolicyGrid({ policies, className = '' }: PolicyGridProps) {
  const router = useRouter();

  if (policies.length === 0) {
    return (
      <div className="text-center py-12">
        <FileText className="w-16 h-16 text-gray-400 mx-auto mb-4" />
        <p className="text-gray-600">No policies uploaded yet</p>
      </div>
    );
  }

  return (
    <div className={`grid md:grid-cols-2 lg:grid-cols-3 gap-6 ${className}`}>
      {policies.map((policy) => (
        <div
          key={policy.id}
          className="bg-white rounded-xl border-2 border-gray-200 hover:border-blue-500 transition-all cursor-pointer group hover:shadow-lg"
          onClick={() => router.push(`/analysis/${policy.id}`)}
        >
          <div className="p-6">
            {/* Status Badge */}
            <div className="flex items-center justify-between mb-4">
              <span
                className={`px-3 py-1 rounded-full text-xs font-semibold ${getStatusColor(
                  policy.status
                )}`}
              >
                {policy.status.replace('_', ' ')}
              </span>
              <div className="flex items-center gap-2 text-gray-400 group-hover:text-blue-600 transition-colors">
                <Eye size={18} />
              </div>
            </div>

            {/* Filename */}
            <div className="flex items-start gap-3 mb-4">
              <FileText className="text-blue-600 flex-shrink-0 mt-1" size={20} />
              <h3 className="font-semibold text-gray-900 truncate">{policy.filename}</h3>
            </div>

            {/* Score */}
            <div className="mb-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-gray-600">Compliance Score</span>
                <span className="text-lg font-bold text-gray-900">{policy.score}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-gradient-to-r from-blue-600 to-indigo-600 h-2 rounded-full transition-all"
                  style={{ width: `${policy.score}%` }}
                />
              </div>
            </div>

            {/* Dates */}
            <div className="text-xs text-gray-500 space-y-1">
              <p>Uploaded: {new Date(policy.uploadedAt).toLocaleDateString()} UTC</p>
              <p>Analyzed: {new Date(policy.lastAnalyzed).toLocaleDateString()} UTC</p>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
