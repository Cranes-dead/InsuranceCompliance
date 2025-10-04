import { CheckCircle } from 'lucide-react';

interface RecommendationListProps {
  recommendations: string[];
  className?: string;
}

export default function RecommendationList({ recommendations, className = '' }: RecommendationListProps) {
  if (recommendations.length === 0) {
    return (
      <div className={`text-center py-8 ${className}`}>
        <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-3" />
        <p className="text-gray-600">No recommendations needed - policy is fully compliant!</p>
      </div>
    );
  }

  return (
    <div className={`space-y-3 ${className}`}>
      {recommendations.map((recommendation, index) => (
        <div
          key={index}
          className="flex items-start gap-3 p-4 bg-blue-50 rounded-lg border border-blue-200"
        >
          <div className="flex-shrink-0 w-6 h-6 rounded-full bg-blue-500 text-white flex items-center justify-center text-sm font-bold mt-0.5">
            {index + 1}
          </div>
          <p className="text-gray-700 flex-1">{recommendation}</p>
        </div>
      ))}
    </div>
  );
}
