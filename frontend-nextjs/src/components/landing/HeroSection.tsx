'use client';

import { ArrowRight, Shield, Sparkles } from 'lucide-react';
import { useRouter } from 'next/navigation';

export default function HeroSection() {
  const router = useRouter();

  return (
    <section className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 via-white to-purple-50">
      <div className="container mx-auto px-4 py-20">
        <div className="text-center max-w-4xl mx-auto">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 bg-blue-100 text-blue-700 px-4 py-2 rounded-full mb-6">
            <Sparkles className="w-4 h-4" />
            <span className="text-sm font-medium">AI-Powered Compliance Verification</span>
          </div>

          {/* Main Heading */}
          <h1 className="text-5xl md:text-6xl font-bold text-gray-900 mb-6 leading-tight">
            Insurance Policy
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-purple-600">
              {' '}Compliance{' '}
            </span>
            Made Simple
          </h1>

          {/* Subheading */}
          <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
            Verify motor vehicle insurance policies against IRDAI regulations in seconds.
            Get detailed compliance reports with AI-powered analysis.
          </p>

          {/* CTA Buttons */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <button
              onClick={() => router.push('/upload')}
              className="inline-flex items-center justify-center gap-2 bg-blue-600 text-white px-8 py-4 rounded-lg font-semibold hover:bg-blue-700 transition-all shadow-lg hover:shadow-xl"
            >
              Start Analysis
              <ArrowRight className="w-5 h-5" />
            </button>
            
            <button
              onClick={() => router.push('/dashboard')}
              className="inline-flex items-center justify-center gap-2 bg-white text-gray-700 px-8 py-4 rounded-lg font-semibold hover:bg-gray-50 transition-all border-2 border-gray-200"
            >
              <Shield className="w-5 h-5" />
              View Dashboard
            </button>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-3 gap-8 mt-16 max-w-2xl mx-auto">
            <div>
              <div className="text-3xl font-bold text-blue-600">92%</div>
              <div className="text-sm text-gray-600 mt-1">Accuracy</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-blue-600">&lt;5s</div>
              <div className="text-sm text-gray-600 mt-1">Analysis Time</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-blue-600">203</div>
              <div className="text-sm text-gray-600 mt-1">Regulations</div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
