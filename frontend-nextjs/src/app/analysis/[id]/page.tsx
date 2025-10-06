'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { PolicyAnalysis } from '@/lib/types';
import { api } from '@/lib/api';
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
import toast from 'react-hot-toast';

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
      } catch (err: any) {
        console.error('Error fetching analysis:', err);
        const errorMessage = err.response?.status === 404 
          ? 'Policy not found. It may have been deleted or the server was restarted.'
          : err.response?.data?.detail || 'Failed to load analysis';
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
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-50 p-8">
        <div className="max-w-7xl mx-auto">
          {/* Header Skeleton */}
          <div className="mb-8">
            <div className="h-4 w-24 bg-gray-200 rounded animate-pulse mb-4" />
            <div className="h-8 w-64 bg-gray-200 rounded animate-pulse" />
          </div>

          {/* Card Skeleton */}
          <div className="bg-white rounded-2xl shadow-xl p-8">
            <div className="space-y-6">
              <div className="h-12 bg-gray-200 rounded animate-pulse" />
              <div className="h-64 bg-gray-200 rounded animate-pulse" />
              <div className="h-32 bg-gray-200 rounded animate-pulse" />
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error || !analysis) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-50 p-8 flex items-center justify-center">
        <div className="bg-white rounded-2xl shadow-xl p-12 max-w-lg text-center">
          <AlertTriangle className="w-16 h-16 text-amber-500 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Policy Analysis Not Found</h2>
          <p className="text-gray-600 mb-4">{error || 'The requested analysis could not be found.'}</p>
          
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6 text-left">
            <p className="text-sm text-blue-900 font-medium mb-2">💡 Why did this happen?</p>
            <ul className="text-sm text-blue-800 space-y-1 list-disc list-inside">
              <li>The server was restarted (policies are stored in memory)</li>
              <li>The policy was deleted</li>
              <li>The policy ID is incorrect</li>
            </ul>
          </div>

          <div className="flex gap-3 justify-center">
            <button
              onClick={() => router.push('/upload')}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Upload New Policy
            </button>
            <button
              onClick={() => router.push('/dashboard')}
              className="px-6 py-3 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
            >
              Back to Dashboard
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-50 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <button
            onClick={() => router.push('/dashboard')}
            className="flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-4 transition-colors"
          >
            <ArrowLeft size={20} />
            <span>Back to Dashboard</span>
          </button>
          <h1 className="text-4xl font-bold text-gray-900">Analysis Results</h1>
        </div>

        {/* Main Content */}
        <div className="space-y-6">
          {/* Overview Card */}
          <div className="bg-white rounded-2xl shadow-xl p-8">
            <div className="grid md:grid-cols-2 gap-8">
              {/* Left: Status & Info */}
              <div className="space-y-6">
                <div>
                  <div className="flex items-center gap-3 mb-4">
                    <FileText className="text-blue-600" size={24} />
                    <h2 className="text-2xl font-bold text-gray-900">{analysis.filename}</h2>
                  </div>
                  <StatusBadge status={analysis.classification} className="mb-4" />
                </div>

                <div className="space-y-4">
                  <div className="flex items-center gap-3 text-gray-600">
                    <TrendingUp size={20} />
                    <div>
                      <p className="text-sm">Confidence</p>
                      <p className="text-2xl font-bold text-gray-900">
                        {(analysis.confidence * 100).toFixed(1)}%
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-3 text-gray-600">
                    <Clock size={20} />
                    <div>
                      <p className="text-sm">Analyzed</p>
                      <p className="font-semibold text-gray-900">
                        {new Date(analysis.created_at).toLocaleString()} UTC
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-3 text-gray-600">
                    <Database size={20} />
                    <div>
                      <p className="text-sm">Regulations Analyzed</p>
                      <p className="font-semibold text-gray-900">
                        {analysis.rag_metadata.regulations_retrieved} regulations
                      </p>
                    </div>
                  </div>
                </div>

                <button
                  onClick={() => router.push(`/chat/${id}`)}
                  className="w-full flex items-center justify-center gap-2 px-6 py-3 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-lg hover:from-blue-700 hover:to-indigo-700 transition-all shadow-lg hover:shadow-xl"
                >
                  <MessageSquare size={20} />
                  <span className="font-semibold">Chat about this policy</span>
                </button>
              </div>

              {/* Right: Compliance Score */}
              <div className="flex items-center justify-center">
                <ScoreGauge score={analysis.compliance_score} label="Compliance Score" />
              </div>
            </div>
          </div>

          {/* Explanation */}
          <div className="bg-white rounded-2xl shadow-xl p-8">
            <h3 className="text-xl font-bold text-gray-900 mb-4">Analysis Summary</h3>
            <p className="text-gray-700 leading-relaxed">{analysis.explanation}</p>
          </div>

          {/* Violations */}
          {analysis.violations.length > 0 && (
            <div className="bg-white rounded-2xl shadow-xl p-8">
              <div className="flex items-center gap-3 mb-6">
                <AlertTriangle className="text-red-600" size={24} />
                <h3 className="text-xl font-bold text-gray-900">
                  Violations Found ({analysis.violations.length})
                </h3>
              </div>
              <div className="space-y-4">
                {analysis.violations.map((violation, index) => (
                  <ViolationCard key={index} violation={violation} />
                ))}
              </div>
            </div>
          )}

          {/* Recommendations */}
          <div className="bg-white rounded-2xl shadow-xl p-8">
            <h3 className="text-xl font-bold text-gray-900 mb-6">Recommendations</h3>
            <RecommendationList recommendations={analysis.recommendations} />
          </div>

          {/* RAG Metadata */}
          {analysis.rag_metadata && Object.keys(analysis.rag_metadata).length > 0 && (
            <div className="bg-white rounded-2xl shadow-xl p-8">
              <h3 className="text-xl font-bold text-gray-900 mb-6">Analysis Metadata</h3>
              <div className="grid md:grid-cols-2 gap-6">
                {/* Regulations Retrieved */}
                {analysis.rag_metadata.regulations_retrieved !== undefined && (
                  <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center">
                        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                      </div>
                      <div>
                        <p className="text-sm text-gray-600">Regulations Analyzed</p>
                        <p className="text-2xl font-bold text-gray-900">{analysis.rag_metadata.regulations_retrieved || 0}</p>
                      </div>
                    </div>
                  </div>
                )}

                {/* Compliance Score */}
                {analysis.rag_metadata.compliance_score !== undefined && (
                  <div className="p-4 bg-green-50 rounded-lg border border-green-200">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-full bg-green-100 text-green-600 flex items-center justify-center">
                        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                      </div>
                      <div>
                        <p className="text-sm text-gray-600">Compliance Score</p>
                        <p className="text-2xl font-bold text-gray-900">{analysis.rag_metadata.compliance_score}%</p>
                      </div>
                    </div>
                  </div>
                )}

                {/* Top Sources */}
                {analysis.rag_metadata.top_sources && Array.isArray(analysis.rag_metadata.top_sources) && analysis.rag_metadata.top_sources.length > 0 && (
                  <div className="md:col-span-2">
                    <h4 className="text-lg font-semibold text-gray-900 mb-4">Referenced Regulations</h4>
                    <div className="grid md:grid-cols-2 gap-4">
                      {analysis.rag_metadata.top_sources.map((source: string, index: number) => (
                        <div
                          key={index}
                          className="p-4 bg-gray-50 rounded-lg border border-gray-200"
                        >
                          <div className="flex items-center gap-2">
                            <div className="w-8 h-8 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center text-sm font-bold">
                              {index + 1}
                            </div>
                            <p className="text-sm text-gray-700 font-mono">{source}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
