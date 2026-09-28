'use client';

import React from 'react';
import Link from 'next/link';
import DashboardLayout from '@/components/layout/DashboardLayout';
import SupportRecommendationsPanel from '@/components/dashboard/SupportRecommendationsPanel';
import { HeartPulse, ArrowLeft, Info } from 'lucide-react';

export default function RecommendationsPage() {
  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Navigation & Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="flex items-center space-x-3">
            <Link
              href="/dashboard"
              className="p-2 bg-surfaceHighlight hover:bg-surfaceHighlight/80 rounded-xl text-textSecondary hover:text-textPrimary transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
            </Link>
            <div>
              <div className="flex items-center space-x-2">
                <h1 className="text-xl font-bold tracking-tight text-textPrimary uppercase">
                  Welfare Recommendations & Interventions
                </h1>
                <span className="px-2 py-0.5 rounded text-[10px] font-mono font-semibold bg-alert-amberBg text-alert-amberText border border-alert-amberBorder">
                  Protocol Pipeline
                </span>
              </div>
              <p className="text-xs text-textSecondary mt-0.5 font-mono">
                AI-guided actionable welfare interventions, non-punitive rest orders, and counseling pipelines
              </p>
            </div>
          </div>
        </div>

        {/* Ethical Framework Banner */}
        <div className="p-3 bg-surface border border-surfaceBorder rounded-xl text-xs text-textSecondary flex items-start space-x-2.5 shadow-card">
          <Info className="w-4 h-4 text-accent shrink-0 mt-0.5" />
          <p className="leading-relaxed">
            <strong className="text-textPrimary">Command Authority Protocol:</strong> Interventions generated here are algorithmic decision-support recommendations designed to protect troop well-being. Action statuses require explicit Welfare Officer or Commander acknowledgment and follow defense welfare standard operating procedures.
          </p>
        </div>

        {/* Full Support Recommendations Panel */}
        <SupportRecommendationsPanel />
      </div>
    </DashboardLayout>
  );
}
