'use client';

import {
  PieChart, Pie, Cell,
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  RadialBarChart, RadialBar,
} from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  type ChartConfig,
} from '@/components/ui/chart';

/* ─── Compliance Gauge (Radial) ─── */

interface ComplianceGaugeProps {
  score: number;
  className?: string;
}

const gaugeConfig = {
  score: { label: "Compliance", color: "oklch(0.60 0.22 285)" },
} satisfies ChartConfig;

export function ComplianceGauge({ score, className = '' }: ComplianceGaugeProps) {
  const data = [{ name: 'Score', value: score, fill: 'var(--color-score)' }];

  return (
    <Card className={className}>
      <CardHeader className="pb-0">
        <CardTitle className="text-sm font-sans font-medium text-muted-foreground">
          Overall Compliance
        </CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col items-center justify-center pb-4">
        <ChartContainer config={gaugeConfig} className="mx-auto aspect-square max-h-[160px] w-full">
          <RadialBarChart
            data={data}
            startAngle={210}
            endAngle={-30}
            innerRadius="70%"
            outerRadius="100%"
            barSize={14}
          >
            <RadialBar
              dataKey="value"
              background={{ fill: 'var(--muted)' }}
              cornerRadius={10}
              max={100}
            />
          </RadialBarChart>
        </ChartContainer>
        <div className="text-center -mt-16 relative z-10">
          <p className="text-5xl font-heading text-foreground tracking-tight">{score}%</p>
          <p className="text-xs text-muted-foreground mt-1">Average Score</p>
        </div>
      </CardContent>
    </Card>
  );
}

/* ─── Status Donut Chart ─── */

interface StatusPieChartProps {
  compliant: number;
  nonCompliant: number;
  review: number;
  className?: string;
}

const statusConfig = {
  compliant: { label: "Compliant", color: "oklch(0.65 0.16 160)" },
  nonCompliant: { label: "Non-Compliant", color: "oklch(0.62 0.20 10)" },
  review: { label: "Review", color: "oklch(0.72 0.14 60)" },
} satisfies ChartConfig;

const STATUS_COLORS = [
  'oklch(0.65 0.16 160)',   // teal-green
  'oklch(0.62 0.20 10)',    // rose
  'oklch(0.72 0.14 60)',    // amber
];

export function StatusPieChart({ compliant, nonCompliant, review, className = '' }: StatusPieChartProps) {
  const data = [
    { name: 'compliant', value: compliant, fill: 'var(--color-compliant)' },
    { name: 'nonCompliant', value: nonCompliant, fill: 'var(--color-nonCompliant)' },
    { name: 'review', value: review, fill: 'var(--color-review)' },
  ];
  const total = compliant + nonCompliant + review;

  return (
    <Card className={className}>
      <CardHeader className="pb-0">
        <CardTitle className="text-sm font-sans font-medium text-muted-foreground">
          Status Distribution
        </CardTitle>
      </CardHeader>
      <CardContent className="pb-4">
        <ChartContainer config={statusConfig} className="mx-auto aspect-square max-h-[180px]">
          <PieChart>
            <ChartTooltip content={<ChartTooltipContent hideLabel />} />
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius="55%"
              outerRadius="85%"
              paddingAngle={3}
              dataKey="value"
              strokeWidth={0}
              cornerRadius={4}
            >
              {data.map((entry, index) => (
                <Cell key={entry.name} fill={STATUS_COLORS[index]} />
              ))}
            </Pie>
          </PieChart>
        </ChartContainer>
        {/* Center label */}
        <div className="text-center -mt-[106px] relative z-10 pointer-events-none">
          <p className="text-3xl font-heading text-foreground">{total}</p>
          <p className="text-[10px] text-muted-foreground">Total</p>
        </div>
        {/* Legend */}
        <div className="flex justify-center gap-4 mt-16 pt-2">
          {[
            { label: 'Compliant', value: compliant, color: STATUS_COLORS[0] },
            { label: 'Non-Compliant', value: nonCompliant, color: STATUS_COLORS[1] },
            { label: 'Review', value: review, color: STATUS_COLORS[2] },
          ].map((item) => (
            <div key={item.label} className="flex items-center gap-1.5">
              <div className="size-2 rounded-full" style={{ backgroundColor: item.color }} />
              <span className="text-[10px] text-muted-foreground">{item.label} ({item.value})</span>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

/* ─── Violation Bar Chart ─── */

interface ViolationBarChartProps {
  data: { name: string; count: number }[];
  className?: string;
}

const SEVERITY_COLORS: Record<string, string> = {
  Critical: 'oklch(0.62 0.22 10)',
  High: 'oklch(0.68 0.16 35)',
  Medium: 'oklch(0.72 0.14 60)',
  Low: 'oklch(0.65 0.16 280)',
};

const violationConfig = {
  count: { label: "Violations", color: "var(--chart-1)" },
} satisfies ChartConfig;

export function ViolationBarChart({ data, className = '' }: ViolationBarChartProps) {
  const coloredData = data.map(d => ({
    ...d,
    fill: SEVERITY_COLORS[d.name] || 'var(--chart-1)',
  }));

  return (
    <Card className={className}>
      <CardHeader className="pb-0">
        <CardTitle className="text-sm font-sans font-medium text-muted-foreground">
          Violation Breakdown
        </CardTitle>
      </CardHeader>
      <CardContent className="pb-4">
        <ChartContainer config={violationConfig} className="h-[200px] w-full">
          <BarChart
            data={coloredData}
            margin={{ top: 8, right: 8, left: -12, bottom: 0 }}
            barCategoryGap="20%"
          >
            <CartesianGrid vertical={false} strokeDasharray="3 3" className="stroke-border/40" />
            <XAxis
              dataKey="name"
              tickLine={false}
              axisLine={false}
              fontSize={11}
              tickMargin={8}
              className="fill-muted-foreground"
            />
            <YAxis
              tickLine={false}
              axisLine={false}
              fontSize={11}
              width={28}
              className="fill-muted-foreground"
            />
            <ChartTooltip
              cursor={{ fill: 'var(--muted)', opacity: 0.3 }}
              content={<ChartTooltipContent />}
            />
            <Bar
              dataKey="count"
              radius={[6, 6, 0, 0]}
              fillOpacity={0.9}
            >
              {coloredData.map((entry, index) => (
                <Cell key={index} fill={entry.fill} />
              ))}
            </Bar>
          </BarChart>
        </ChartContainer>
      </CardContent>
    </Card>
  );
}
