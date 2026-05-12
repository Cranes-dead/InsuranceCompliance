'use client';

import { ArrowRight, Shield, Sparkles } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { motion } from 'framer-motion';

export default function HeroSection() {
  const router = useRouter();

  return (
    <section className="relative overflow-hidden">
      {/* Subtle gradient bg */}
      <div className="absolute inset-0 bg-gradient-to-br from-chart-1/5 via-background to-chart-4/5" />
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-chart-1/10 via-transparent to-transparent" />

      <div className="relative container mx-auto px-4 py-24 md:py-32 lg:py-40">
        <div className="text-center max-w-4xl mx-auto">
          {/* Badge */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <Badge variant="secondary" className="mb-6 gap-1.5 px-3 py-1.5 text-xs">
              <Sparkles className="size-3" />
              AI-Powered Compliance Verification
            </Badge>
          </motion.div>

          {/* Main Heading */}
          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="text-5xl md:text-6xl lg:text-7xl font-heading text-foreground mb-6 leading-[1.1] tracking-tight"
          >
            Insurance Policy{' '}
            <span className="text-chart-1">
              Compliance
            </span>{' '}
            Made Simple
          </motion.h1>

          {/* Subheading */}
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="text-lg md:text-xl text-muted-foreground mb-10 max-w-2xl mx-auto leading-relaxed"
          >
            Verify motor vehicle insurance policies against IRDAI regulations in seconds.
            Get detailed compliance reports with AI-powered analysis.
          </motion.p>

          {/* CTA Buttons */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.3 }}
            className="flex flex-col sm:flex-row gap-3 justify-center"
          >
            <Button
              size="lg"
              onClick={() => router.push('/upload')}
              className="gap-2 px-8 text-base"
            >
              Start Analysis
              <ArrowRight className="size-4" />
            </Button>

            <Button
              variant="outline"
              size="lg"
              onClick={() => router.push('/dashboard')}
              className="gap-2 px-8 text-base"
            >
              <Shield className="size-4" />
              View Dashboard
            </Button>
          </motion.div>

          {/* Stats */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.4 }}
            className="grid grid-cols-3 gap-8 mt-20 max-w-lg mx-auto"
          >
            {[
              { value: '92%', label: 'Accuracy' },
              { value: '<5s', label: 'Analysis Time' },
              { value: '203', label: 'Regulations' },
            ].map((stat) => (
              <div key={stat.label} className="text-center">
                <div className="text-3xl md:text-4xl font-heading text-foreground">
                  {stat.value}
                </div>
                <div className="text-xs text-muted-foreground mt-1 uppercase tracking-wider">
                  {stat.label}
                </div>
              </div>
            ))}
          </motion.div>
        </div>
      </div>
    </section>
  );
}
