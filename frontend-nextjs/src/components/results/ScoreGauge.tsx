interface ScoreGaugeProps {
  score: number;
  label: string;
  className?: string;
}

export default function ScoreGauge({ score, label, className = '' }: ScoreGaugeProps) {
  const radius = 80;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;

  const getColor = () => {
    if (score >= 80) return '#22c55e'; // green
    if (score >= 60) return '#eab308'; // yellow
    return '#ef4444'; // red
  };

  return (
    <div className={`flex flex-col items-center ${className}`}>
      <div className="relative w-48 h-48">
        <svg className="w-full h-full transform -rotate-90">
          {/* Background circle */}
          <circle
            cx="96"
            cy="96"
            r={radius}
            stroke="#e5e7eb"
            strokeWidth="12"
            fill="none"
          />
          {/* Progress circle */}
          <circle
            cx="96"
            cy="96"
            r={radius}
            stroke={getColor()}
            strokeWidth="12"
            fill="none"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            strokeLinecap="round"
            className="transition-all duration-1000 ease-out"
          />
        </svg>
        {/* Score text */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-4xl font-bold" style={{ color: getColor() }}>
            {score}%
          </span>
          <span className="text-sm text-gray-500 mt-1">{label}</span>
        </div>
      </div>
    </div>
  );
}
