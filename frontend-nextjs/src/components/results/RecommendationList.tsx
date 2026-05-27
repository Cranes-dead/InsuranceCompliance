import { CheckCircle } from 'lucide-react';
import { Card } from '@/components/ui/card';

interface RecommendationListProps {
  recommendations: string[];
  className?: string;
}

export default function RecommendationList({ recommendations, className = '' }: RecommendationListProps) {
  if (recommendations.length === 0) {
    return (
      <div className={`text-center py-8 ${className}`}>
        <CheckCircle className="size-10 text-emerald-500 dark:text-emerald-400 mx-auto mb-3" />
        <p className="text-sm text-muted-foreground">No recommendations needed — policy is fully compliant!</p>
      </div>
    );
  }

  return (
    <div className={`space-y-2 ${className}`}>
      {recommendations.map((recommendation, index) => (
        <Card
          key={index}
          className="p-3 flex items-start gap-3 border-chart-1/20 bg-chart-1/5"
        >
          <div className="flex-shrink-0 size-5 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-[10px] font-semibold mt-0.5">
            {index + 1}
          </div>
          <p className="text-sm text-foreground/80 leading-relaxed flex-1">{recommendation}</p>
        </Card>
      ))}
    </div>
  );
}
