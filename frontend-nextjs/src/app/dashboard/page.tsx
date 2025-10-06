'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { DashboardStats, Policy } from '@/lib/types';
import { api } from '@/lib/api';
import { FileText, CheckCircle, XCircle, AlertCircle, Upload, TrendingUp } from 'lucide-react';
import PolicyGrid from '@/components/dashboard/PolicyGrid';
import { ComplianceGauge, StatusPieChart, ViolationBarChart } from '@/components/dashboard/Charts';
import toast from 'react-hot-toast';

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
      } catch (error: any) {
        console.error('Error fetching dashboard data:', error);
        toast.error('Failed to load dashboard data');
        // Set empty data on error
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
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-50 p-8">
        <div className="max-w-7xl mx-auto">
          <div className="h-8 w-64 bg-gray-200 rounded animate-pulse mb-8" />
          <div className="grid md:grid-cols-4 gap-6 mb-8">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="bg-white rounded-xl shadow-lg p-6 h-32 animate-pulse" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  // Mock violation data for chart (you can get this from backend)
  const violationData = [
    { name: 'Critical', count: 5 },
    { name: 'High', count: 12 },
    { name: 'Medium', count: 23 },
    { name: 'Low', count: 8 }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-50 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold text-gray-900 mb-2">Policy Dashboard</h1>
            <p className="text-gray-600">Manage and monitor your insurance policies</p>
          </div>
          <button
            onClick={() => router.push('/upload')}
            className="px-6 py-3 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-lg hover:from-blue-700 hover:to-indigo-700 transition-all shadow-lg hover:shadow-xl flex items-center gap-2"
          >
            <Upload size={20} />
            <span>Upload Policy</span>
          </button>
        </div>

        {/* Stats Grid */}
        <div className="grid md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition-shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm">Total Policies</p>
                <p className="text-3xl font-bold text-gray-900">{stats?.totalPolicies || 0}</p>
              </div>
              <FileText className="text-blue-600" size={40} />
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition-shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm">Compliant</p>
                <p className="text-3xl font-bold text-green-600">{stats?.compliantPolicies || 0}</p>
              </div>
              <CheckCircle className="text-green-600" size={40} />
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition-shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm">Non-Compliant</p>
                <p className="text-3xl font-bold text-red-600">{stats?.nonCompliantPolicies || 0}</p>
              </div>
              <XCircle className="text-red-600" size={40} />
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition-shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm">Review Required</p>
                <p className="text-3xl font-bold text-yellow-600">{stats?.reviewRequired || 0}</p>
              </div>
              <AlertCircle className="text-yellow-600" size={40} />
            </div>
          </div>
        </div>

        {stats && stats.totalPolicies === 0 ? (
          /* Empty State */
          <div className="bg-white rounded-2xl shadow-xl p-12 text-center">
            <Upload className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-2xl font-bold text-gray-900 mb-2">No Policies Yet</h3>
            <p className="text-gray-600 mb-6">Upload your first insurance policy to get started</p>
            <button
              onClick={() => router.push('/upload')}
              className="px-6 py-3 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-lg hover:from-blue-700 hover:to-indigo-700 transition-all shadow-lg hover:shadow-xl"
            >
              Upload Policy
            </button>
          </div>
        ) : (
          <>
            {/* Charts Section */}
            <div className="grid md:grid-cols-3 gap-6 mb-8">
              {/* Compliance Gauge */}
              <div className="bg-white rounded-xl shadow-lg p-6">
                <div className="flex items-center gap-2 mb-4">
                  <TrendingUp className="text-blue-600" size={24} />
                  <h3 className="text-lg font-bold text-gray-900">Overall Compliance</h3>
                </div>
                <ComplianceGauge score={stats?.averageScore || 0} />
              </div>

              {/* Status Distribution */}
              <div className="bg-white rounded-xl shadow-lg p-6">
                <h3 className="text-lg font-bold text-gray-900 mb-4">Status Distribution</h3>
                <StatusPieChart
                  compliant={stats?.compliantPolicies || 0}
                  nonCompliant={stats?.nonCompliantPolicies || 0}
                  review={stats?.reviewRequired || 0}
                />
              </div>

              {/* Violation Frequency */}
              <div className="bg-white rounded-xl shadow-lg p-6">
                <h3 className="text-lg font-bold text-gray-900 mb-4">Violation Breakdown</h3>
                <ViolationBarChart data={violationData} />
              </div>
            </div>

            {/* Recent Analyses Table */}
            {stats?.recentAnalyses && stats.recentAnalyses.length > 0 && (
              <div className="bg-white rounded-xl shadow-lg p-6 mb-8">
                <h3 className="text-lg font-bold text-gray-900 mb-4">Recent Analyses</h3>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-gray-200">
                        <th className="text-left py-3 px-4 text-sm font-semibold text-gray-600">Policy</th>
                        <th className="text-left py-3 px-4 text-sm font-semibold text-gray-600">Status</th>
                        <th className="text-left py-3 px-4 text-sm font-semibold text-gray-600">Score</th>
                        <th className="text-left py-3 px-4 text-sm font-semibold text-gray-600">Date</th>
                        <th className="text-left py-3 px-4 text-sm font-semibold text-gray-600">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {stats.recentAnalyses.map((analysis) => (
                        <tr key={analysis.id} className="border-b border-gray-100 hover:bg-gray-50">
                          <td className="py-3 px-4 text-sm text-gray-900">{analysis.filename}</td>
                          <td className="py-3 px-4">
                            <span className={`px-2 py-1 rounded-full text-xs font-semibold ${
                              analysis.classification === 'COMPLIANT' ? 'bg-green-100 text-green-800' :
                              analysis.classification === 'NON_COMPLIANT' ? 'bg-red-100 text-red-800' :
                              'bg-yellow-100 text-yellow-800'
                            }`}>
                              {analysis.classification.replace('_', ' ')}
                            </span>
                          </td>
                          <td className="py-3 px-4 text-sm font-semibold text-gray-900">
                            {analysis.compliance_score}%
                          </td>
                          <td className="py-3 px-4 text-sm text-gray-600">
                            {new Date(analysis.created_at).toLocaleDateString()} UTC
                          </td>
                          <td className="py-3 px-4">
                            <button
                              onClick={() => router.push(`/analysis/${analysis.id}`)}
                              className="text-blue-600 hover:text-blue-800 text-sm font-semibold"
                            >
                              View Details
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Policy Portfolio */}
            <div className="bg-white rounded-xl shadow-lg p-6">
              <h3 className="text-lg font-bold text-gray-900 mb-4">Policy Portfolio</h3>
              <PolicyGrid policies={policies} />
            </div>
          </>
        )}
      </div>
    </div>
  );
}
