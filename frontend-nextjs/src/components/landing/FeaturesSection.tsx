'use client';

import { Brain, Zap, Shield, MessageSquare, FileCheck, TrendingUp } from 'lucide-react';

const features = [
  {
    icon: Brain,
    title: 'AI-Powered Analysis',
    description: 'Legal-BERT + RAG + LLaMA 3.1 for intelligent compliance checking',
    color: 'text-blue-600',
    bgColor: 'bg-blue-100',
  },
  {
    icon: Zap,
    title: 'Instant Results',
    description: 'Get comprehensive compliance reports in under 5 seconds',
    color: 'text-yellow-600',
    bgColor: 'bg-yellow-100',
  },
  {
    icon: Shield,
    title: '203 Regulations',
    description: 'Verified against complete IRDAI and MoRTH regulatory database',
    color: 'text-green-600',
    bgColor: 'bg-green-100',
  },
  {
    icon: MessageSquare,
    title: 'Interactive Chat',
    description: 'Ask questions about your policy and get AI-powered answers',
    color: 'text-purple-600',
    bgColor: 'bg-purple-100',
  },
  {
    icon: FileCheck,
    title: 'Detailed Reports',
    description: 'Violations, recommendations, and regulatory citations included',
    color: 'text-red-600',
    bgColor: 'bg-red-100',
  },
  {
    icon: TrendingUp,
    title: 'Dashboard Analytics',
    description: 'Track compliance trends and manage multiple policies',
    color: 'text-indigo-600',
    bgColor: 'bg-indigo-100',
  },
];

export default function FeaturesSection() {
  return (
    <section className="py-20 bg-white">
      <div className="container mx-auto px-4">
        {/* Section Header */}
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="text-4xl font-bold text-gray-900 mb-4">
            Why Choose Our System?
          </h2>
          <p className="text-lg text-gray-600">
            Powered by cutting-edge AI technology for accurate, fast, and explainable compliance verification
          </p>
        </div>

        {/* Features Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8 max-w-6xl mx-auto">
          {features.map((feature, index) => {
            const Icon = feature.icon;
            return (
              <div
                key={index}
                className="p-6 rounded-xl border-2 border-gray-100 hover:border-blue-200 hover:shadow-lg transition-all"
              >
                <div className={`w-12 h-12 ${feature.bgColor} rounded-lg flex items-center justify-center mb-4`}>
                  <Icon className={`w-6 h-6 ${feature.color}`} />
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">
                  {feature.title}
                </h3>
                <p className="text-gray-600">
                  {feature.description}
                </p>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
