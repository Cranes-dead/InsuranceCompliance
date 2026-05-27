'use client';

import { Brain, Zap, Shield, MessageSquare, FileCheck, TrendingUp } from 'lucide-react';
import { Card, CardHeader, CardContent } from '@/components/ui/card';
import { motion } from 'framer-motion';

const features = [
  {
    icon: Brain,
    title: 'AI-Powered Analysis',
    description: 'Legal-BERT + RAG + LLaMA 3.1 for intelligent compliance checking',
    glow: 'bg-emerald-500'
  },
  {
    icon: Zap,
    title: 'Instant Results',
    description: 'Get comprehensive compliance reports in under 5 seconds',
    glow: 'bg-amber-500'
  },
  {
    icon: Shield,
    title: '203 Regulations',
    description: 'Verified against complete IRDAI and MoRTH regulatory database',
    glow: 'bg-rose-500'
  },
  {
    icon: MessageSquare,
    title: 'Interactive Chat',
    description: 'Ask questions about your policy and get AI-powered answers',
    glow: 'bg-chart-1'
  },
  {
    icon: FileCheck,
    title: 'Detailed Reports',
    description: 'Violations, recommendations, and regulatory citations included',
    glow: 'bg-chart-2'
  },
  {
    icon: TrendingUp,
    title: 'Dashboard Analytics',
    description: 'Track compliance trends and manage multiple policies',
    glow: 'bg-chart-3'
  },
];

export default function FeaturesSection() {
  return (
    <section className="py-20 md:py-28 bg-muted/30">
      <div className="container mx-auto px-4">
        {/* Section Header */}
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="text-4xl md:text-5xl font-heading text-foreground mb-5 tracking-tight">
            Why Choose Our System?
          </h2>
          <p className="text-muted-foreground text-lg font-sans">
            Powered by cutting-edge AI technology for accurate, fast, and explainable compliance verification
          </p>
        </div>

        {/* Features Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-6xl mx-auto">
          {features.map((feature, index) => {
            const Icon = feature.icon;
            return (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                className="h-full"
              >
                <Card className="group relative overflow-hidden h-full p-6 border-border/40 bg-card/40 backdrop-blur-md cursor-pointer transition-all duration-500 hover:shadow-2xl hover:shadow-background/50 hover:-translate-y-1 hover:border-border/80 hover:bg-card/80">


                  <CardHeader className="pb-4 px-0 pt-0">
                    <motion.div 
                      className="size-12 rounded-xl bg-muted/40 flex items-center justify-center mb-4 border border-border/50 shadow-inner group-hover:bg-primary/5 transition-colors duration-500"
                      whileHover={{ scale: 1.1, rotate: 8 }}
                      transition={{ duration: 0.4, type: "spring", bounce: 0.5 }}
                    >
                      <Icon className="size-5 text-foreground/70 group-hover:text-primary transition-colors duration-300" />
                    </motion.div>
                    <h3 className="text-lg font-medium text-foreground font-sans line-clamp-1 group-hover:text-primary group-hover:translate-x-1 transition-all duration-300">
                      {feature.title}
                    </h3>
                  </CardHeader>
                  <CardContent className="px-0 pb-0">
                    <p className="text-sm text-muted-foreground leading-relaxed">
                      {feature.description}
                    </p>
                  </CardContent>
                </Card>
              </motion.div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
