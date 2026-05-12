'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { DashboardStats, Policy } from '@/lib/types';
import { api } from '@/lib/api';
import { FileText, CheckCircle, XCircle, AlertCircle, Upload } from 'lucide-react';
import Navbar from '@/components/layout/Navbar';
import PolicyGrid from '@/components/dashboard/PolicyGrid';
import { ComplianceGauge, StatusPieChart, ViolationBarChart } from '@/components/dashboard/Charts';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { getStatusLabel, getStatusColor } from '@/lib/utils';

export default function DashboardPage() {
  const router = useRouter();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [policies, setPolicies] = useState<Policy[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setLoading(true);
        const [statsData, policiesData] = await Promise.all([
          api.getStatistics(),
          api.getAllPolicies()
        ]);
        setStats(statsData);
        setPolicies(policiesData);
      } catch (error: unknown) {
        console.error('Error fetching dashboard data:', error);
        toast.error('Failed to load dashboard data');
        setStats({
          totalPolicies: 0,
          compliantPolicies: 0,
          nonCompliantPolicies: 0,
          reviewRequired: 0,
          averageScore: 0,
          recentAnalyses: []
        });
        setPolicies([]);
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-background">
        <Navbar />
        <div className="container mx-auto px-4 py-8">
          <Skeleton className="h-8 w-64 mb-8" />
          <div className="grid md:grid-cols-4 gap-4 mb-8">
            {[...Array(4)].map((_, i) => (
              <Skeleton key={i} className="h-24 rounded-lg" />
            ))}
          </div>
          <div className="grid md:grid-cols-3 gap-4">
            {[...Array(3)].map((_, i) => (
              <Skeleton key={i} className="h-72 rounded-lg" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  const violationData = [
    { name: 'Critical', count: 5 },
    { name: 'High', count: 12 },
    { name: 'Medium', count: 23 },
    { name: 'Low', count: 8 }
  ];

  const statCards = [
    { label: 'Total Policies', value: stats?.totalPolicies || 0, icon: FileText, color: 'text-primary' },
    { label: 'Compliant', value: stats?.compliantPolicies || 0, icon: CheckCircle, color: 'text-emerald-600 dark:text-emerald-400' },
    { label: 'Non-Compliant', value: stats?.nonCompliantPolicies || 0, icon: XCircle, color: 'text-destructive' },
    { label: 'Review Required', value: stats?.reviewRequired || 0, icon: AlertCircle, color: 'text-amber-600 dark:text-amber-400' },
  ];

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-heading text-foreground mb-1">Policy Dashboard</h1>
            <p className="text-sm text-muted-foreground">Manage and monitor your insurance policies</p>
          </div>
          <Button onClick={() => router.push('/upload')} size="sm" className="gap-1.5">
            <Upload className="size-3.5" />
            Upload Policy
          </Button>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          {statCards.map((stat) => {
            const Icon = stat.icon;
            return (
              <Card key={stat.label}>
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-xs text-muted-foreground">{stat.label}</p>
                      <p className="text-2xl font-semibold tabular-nums text-foreground mt-1">{stat.value}</p>
                    </div>
                    <Icon className={`size-8 ${stat.color} opacity-80`} />
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>

        {stats && stats.totalPolicies === 0 ? (
          /* Empty State */
          <Card className="p-12 text-center">
            <Upload className="size-12 text-muted-foreground/40 mx-auto mb-3" />
            <h3 className="text-xl font-heading text-foreground mb-2">No Policies Yet</h3>
            <p className="text-sm text-muted-foreground mb-6">Upload your first insurance policy to get started</p>
            <Button onClick={() => router.push('/upload')}>
              Upload Policy
            </Button>
          </Card>
        ) : (
          <>
            {/* Charts Section */}
            <div className="grid md:grid-cols-3 gap-4 mb-8">
              <ComplianceGauge score={stats?.averageScore || 0} />
              <StatusPieChart
                compliant={stats?.compliantPolicies || 0}
                nonCompliant={stats?.nonCompliantPolicies || 0}
                review={stats?.reviewRequired || 0}
              />
              <ViolationBarChart data={violationData} />
            </div>

            {/* Recent Analyses Table */}
            {stats?.recentAnalyses && stats.recentAnalyses.length > 0 && (
              <Card className="mb-8">
                <div className="p-4 border-b border-border">
                  <h3 className="text-xl font-heading text-foreground">Recent Analyses</h3>
                </div>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="text-xs">Policy</TableHead>
                      <TableHead className="text-xs">Status</TableHead>
                      <TableHead className="text-xs">Score</TableHead>
                      <TableHead className="text-xs">Date</TableHead>
                      <TableHead className="text-xs">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {stats.recentAnalyses.map((analysis) => (
                      <TableRow key={analysis.id}>
                        <TableCell className="text-xs font-medium">{analysis.filename}</TableCell>
                        <TableCell>
                          <Badge variant="outline" className={`text-[10px] ${getStatusColor(analysis.classification)}`}>
                            {getStatusLabel(analysis.classification)}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-xs font-semibold tabular-nums">
                          {analysis.compliance_score}%
                        </TableCell>
                        <TableCell className="text-xs text-muted-foreground">
                          {new Date(analysis.created_at).toLocaleDateString()}
                        </TableCell>
                        <TableCell>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="text-xs h-7 text-primary"
                            onClick={() => router.push(`/analysis/${analysis.id}`)}
                          >
                            View
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </Card>
            )}

            {/* Policy Portfolio */}
            <div>
              <h3 className="text-xl font-heading text-foreground mb-4">Policy Portfolio</h3>
              <PolicyGrid policies={policies} />
            </div>
          </>
        )}
      </div>
    </div>
  );
}
