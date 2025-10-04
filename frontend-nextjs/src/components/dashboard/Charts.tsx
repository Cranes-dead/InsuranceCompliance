'use client';

import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from 'recharts';

interface ComplianceGaugeProps {
  score: number;
  className?: string;
}

export function ComplianceGauge({ score, className = '' }: ComplianceGaugeProps) {
  const data = [
    { name: 'Score', value: score },
    { name: 'Remaining', value: 100 - score }
  ];

  const COLORS = ['#22c55e', '#e5e7eb'];

  return (
    <div className={`flex flex-col items-center ${className}`}>
      <ResponsiveContainer width="100%" height={200}>
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            startAngle={180}
            endAngle={0}
            innerRadius={60}
            outerRadius={80}
            dataKey="value"
            strokeWidth={0}
          >
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={COLORS[index]} />
            ))}
          </Pie>
        </PieChart>
      </ResponsiveContainer>
      <div className="text-center -mt-4">
        <p className="text-4xl font-bold text-gray-900">{score}%</p>
        <p className="text-sm text-gray-500">Average Score</p>
      </div>
    </div>
  );
}

interface StatusPieChartProps {
  compliant: number;
  nonCompliant: number;
  review: number;
  className?: string;
}

export function StatusPieChart({ compliant, nonCompliant, review, className = '' }: StatusPieChartProps) {
  const data = [
    { name: 'Compliant', value: compliant, color: '#22c55e' },
    { name: 'Non-Compliant', value: nonCompliant, color: '#ef4444' },
    { name: 'Review Required', value: review, color: '#eab308' }
  ];

  return (
    <div className={className}>
      <ResponsiveContainer width="100%" height={250}>
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            labelLine={false}
            label={({ name, percent }: any) => `${name}: ${(percent * 100).toFixed(0)}%`}
            outerRadius={80}
            fill="#8884d8"
            dataKey="value"
          >
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Pie>
          <Tooltip />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}

interface ViolationBarChartProps {
  data: { name: string; count: number }[];
  className?: string;
}

export function ViolationBarChart({ data, className = '' }: ViolationBarChartProps) {
  return (
    <div className={className}>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data}>
          <XAxis dataKey="name" />
          <YAxis />
          <Tooltip />
          <Bar dataKey="count" fill="#3b82f6" radius={[8, 8, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
