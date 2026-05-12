'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { PolicyAnalysis } from '@/lib/types';
import { api } from '@/lib/api';
import Navbar from '@/components/layout/Navbar';
import StatusBadge from '@/components/results/StatusBadge';
import ScoreGauge from '@/components/results/ScoreGauge';
import ViolationCard from '@/components/results/ViolationCard';
import RecommendationList from '@/components/results/RecommendationList';
import {
  ArrowLeft,
  MessageSquare,
  FileText,
  Clock,
  Database,
  TrendingUp,
  AlertTriangle
} from 'lucide-react';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Separator } from '@/components/ui/separator';

export default function AnalysisPage() {
  const params = useParams();
  const router = useRouter();
  const [analysis, setAnalysis] = useState<PolicyAnalysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const id = params.id as string;

  useEffect(() => {
    const fetchAnalysis = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await api.getAnalysis(id);
        setAnalysis(data);
      } catch (err: unknown) {
        const error = err as { response?: { status?: number; data?: { detail?: string } } };
        console.error('Error fetching analysis:', err);
        const errorMessage = error.response?.status === 404
          ? 'Policy not found. It may have been deleted or the server was restarted.'
          : error.response?.data?.detail || 'Failed to load analysis';
        setError(errorMessage);
        toast.error(errorMessage);
      } finally {
        setLoading(false);
      }
    };

    fetchAnalysis();
  }, [id]);

  if (loading) {
    return (
      <div className="min-h-screen bg-background">
        <Navbar />
        <div className="container mx-auto px-4 py-8 max-w-5xl">
          <Skeleton className="h-6 w-32 mb-4" />
          <Skeleton className="h-8 w-72 mb-8" />
          <Skeleton className="h-64 rounded-lg mb-6" />
          <Skeleton className="h-48 rounded-lg mb-6" />
          <Skeleton className="h-32 rounded-lg" />
        </div>
      </div>
    );
  }

  if (error || !analysis) {
    return (
      <div className="min-h-screen bg-background">
        <Navbar />
        <div className="container mx-auto px-4 py-8 flex items-center justify-center min-h-[60vh]">
          <Card className="max-w-lg text-center p-8">
            <AlertTriangle className="size-12 text-amber-500 mx-auto mb-4" />
            <h2 className="text-2xl font-heading text-foreground mb-2">Policy Analysis Not Found</h2>
            <p className="text-sm text-muted-foreground mb-4">{error || 'The requested analysis could not be found.'}</p>

            <Alert className="text-left mb-6">
              <AlertTriangle className="size-4" />
              <AlertTitle className="font-sans">Why did this happen?</AlertTitle>
              <AlertDescription>
                <ul className="text-xs space-y-1 list-disc list-inside mt-1">
                  <li>The server was restarted (policies are stored in memory)</li>
                  <li>The policy was deleted</li>
                  <li>The policy ID is incorrect</li>
                </ul>
              </AlertDescription>
            </Alert>

            <div className="flex gap-2 justify-center">
              <Button onClick={() => router.push('/upload')}>
                Upload New Policy
              </Button>
              <Button variant="outline" onClick={() => router.push('/dashboard')}>
                Back to Dashboard
              </Button>
            </div>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <div className="container mx-auto px-4 py-8 max-w-5xl">
        {/* Header */}
        <div className="mb-6">
          <Button
            variant="ghost"
            size="sm"
            className="gap-1.5 -ml-2 mb-3 text-muted-foreground hover:text-foreground"
            onClick={() => router.push('/dashboard')}
          >
            <ArrowLeft className="size-3.5" />
            Back to Dashboard
          </Button>
          <h1 className="text-3xl font-heading text-foreground">Analysis Results</h1>
        </div>

        {/* Overview Card */}
        <Card className="mb-6">
          <CardContent className="p-6">
            <div className="grid md:grid-cols-2 gap-8">
              {/* Left: Status & Info */}
              <div className="space-y-5">
                <div>
                  <div className="flex items-center gap-2.5 mb-3">
                    <FileText className="size-5 text-primary" />
                    <h2 className="text-xl font-heading text-foreground">{analysis.filename}</h2>
                  </div>
                  <StatusBadge status={analysis.classification} />
                </div>

                <Separator />

                <div className="space-y-3">
                  <div className="flex items-center gap-3">
                    <TrendingUp className="size-4 text-muted-foreground" />
                    <div>
                      <p className="text-xs text-muted-foreground">Confidence</p>
                      <p className="text-lg font-semibold tabular-nums text-foreground">
                        {(analysis.confidence * 100).toFixed(1)}%
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-3">
                    <Clock className="size-4 text-muted-foreground" />
                    <div>
                      <p className="text-xs text-muted-foreground">Analyzed</p>
                      <p className="text-sm font-medium text-foreground">
                        {new Date(analysis.created_at).toLocaleString()}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-3">
                    <Database className="size-4 text-muted-foreground" />
                    <div>
                      <p className="text-xs text-muted-foreground">Regulations Analyzed</p>
                      <p className="text-sm font-medium text-foreground">
                        {analysis.rag_metadata.regulations_retrieved} regulations
                      </p>
                    </div>
                  </div>
                </div>

                <Button
                  onClick={() => router.push(`/chat/${id}`)}
                  className="w-full gap-2"
                >
                  <MessageSquare className="size-4" />
                  Chat about this policy
                </Button>
              </div>

              {/* Right: Compliance Score */}
              <div className="flex items-center justify-center">
                <ScoreGauge score={analysis.compliance_score} label="Compliance Score" />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Tabbed Content */}
        <Tabs defaultValue="summary" className="space-y-4">
          <TabsList className="w-full justify-start">
            <TabsTrigger value="summary">Summary</TabsTrigger>
            <TabsTrigger value="violations">
              Violations ({analysis.violations.length})
            </TabsTrigger>
            <TabsTrigger value="recommendations">Recommendations</TabsTrigger>
            <TabsTrigger value="metadata">Metadata</TabsTrigger>
          </TabsList>

          <TabsContent value="summary">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg font-heading">Analysis Summary</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-foreground/80 leading-relaxed">{analysis.explanation}</p>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="violations">
            {analysis.violations.length > 0 ? (
              <div className="space-y-3">
                {analysis.violations.map((violation, index) => (
                  <ViolationCard key={index} violation={violation} />
                ))}
              </div>
            ) : (
              <Card className="p-8 text-center">
                <p className="text-sm text-muted-foreground">No violations found</p>
              </Card>
            )}
          </TabsContent>

          <TabsContent value="recommendations">
            <Card>
              <CardHeader>
                <CardTitle className="text-lg font-heading">Recommendations</CardTitle>
              </CardHeader>
              <CardContent>
                <RecommendationList recommendations={analysis.recommendations} />
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="metadata">
            {analysis.rag_metadata && Object.keys(analysis.rag_metadata).length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg font-heading">Analysis Metadata</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid md:grid-cols-2 gap-4">
                    {analysis.rag_metadata.regulations_retrieved !== undefined && (
                      <div className="p-3 bg-chart-1/5 rounded-md border border-chart-1/20">
                        <p className="text-xs text-muted-foreground">Regulations Analyzed</p>
                        <p className="text-xl font-semibold tabular-nums text-foreground mt-0.5">
                          {analysis.rag_metadata.regulations_retrieved || 0}
                        </p>
                      </div>
                    )}

                    {analysis.rag_metadata.compliance_score !== undefined && (
                      <div className="p-3 bg-emerald-500/5 dark:bg-emerald-500/10 rounded-md border border-emerald-500/20">
                        <p className="text-xs text-muted-foreground">Compliance Score</p>
                        <p className="text-xl font-semibold tabular-nums text-foreground mt-0.5">
                          {analysis.rag_metadata.compliance_score}%
                        </p>
                      </div>
                    )}

                    {analysis.rag_metadata.top_sources && Array.isArray(analysis.rag_metadata.top_sources) && analysis.rag_metadata.top_sources.length > 0 && (
                      <div className="md:col-span-2">
                        <h4 className="text-sm font-medium text-foreground font-sans mb-3">Referenced Regulations</h4>
                        <div className="grid md:grid-cols-2 gap-2">
                          {analysis.rag_metadata.top_sources.map((source: string, index: number) => (
                            <div
                              key={index}
                              className="p-2.5 bg-muted/50 rounded-md border border-border/50 flex items-center gap-2"
                            >
                              <div className="size-5 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-[10px] font-semibold flex-shrink-0">
                                {index + 1}
                              </div>
                              <p className="text-xs text-foreground/80 font-mono truncate">{source}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            )}
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
