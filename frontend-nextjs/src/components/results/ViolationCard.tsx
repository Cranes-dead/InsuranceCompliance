import { Violation } from '@/lib/types';
import { AlertTriangle, AlertCircle, Info } from 'lucide-react';

interface ViolationCardProps {
  violation: Violation;
}

export default function ViolationCard({ violation }: ViolationCardProps) {
  const getSeverityConfig = () => {
    switch (violation.severity) {
      case 'CRITICAL':
      case 'HIGH':
        return {
          bg: 'bg-red-50',
          border: 'border-red-200',
          text: 'text-red-800',
          icon: AlertCircle,
          color: '#ef4444'
        };
      case 'MEDIUM':
        return {
          bg: 'bg-yellow-50',
          border: 'border-yellow-200',
          text: 'text-yellow-800',
          icon: AlertTriangle,
          color: '#eab308'
        };
      case 'LOW':
        return {
          bg: 'bg-blue-50',
          border: 'border-blue-200',
          text: 'text-blue-800',
          icon: Info,
          color: '#3b82f6'
        };
      default:
        return {
          bg: 'bg-gray-50',
          border: 'border-gray-200',
          text: 'text-gray-800',
          icon: Info,
          color: '#6b7280'
        };
    }
  };

  const config = getSeverityConfig();
  const Icon = config.icon;

  return (
    <div className={`p-4 rounded-lg border-2 ${config.bg} ${config.border}`}>
      <div className="flex items-start gap-3">
        <Icon className={config.text} size={24} />
        <div className="flex-1">
          <div className="flex items-center justify-between mb-2">
            <h4 className="font-semibold text-gray-900">{violation.regulation_reference}</h4>
            <span className={`text-xs font-bold px-2 py-1 rounded ${config.text} bg-white`}>
              {violation.severity}
            </span>
          </div>
          <p className="text-sm text-gray-600 mb-1">
            <span className="font-semibold">Type: </span>
            {violation.type}
          </p>
          <p className="text-gray-700 mb-2">{violation.description}</p>
          {violation.recommendation && (
            <div className="mt-3 p-3 bg-white rounded border border-gray-200">
              <p className="text-sm text-gray-600">
                <span className="font-semibold">Recommendation: </span>
                {violation.recommendation}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
