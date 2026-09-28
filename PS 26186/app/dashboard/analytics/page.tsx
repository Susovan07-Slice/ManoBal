'use client';

import React from 'react';
import Link from 'next/link';
import DashboardLayout from '@/components/layout/DashboardLayout';
import AdvancedCommanderAnalytics from '@/components/dashboard/AdvancedCommanderAnalytics';
import { BarChart3, ArrowLeft, ShieldCheck } from 'lucide-react';

export default function AnalyticsPage() {
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
                  Unit Welfare Analytics & Intelligence
                </h1>
                <span className="px-2 py-0.5 rounded text-[10px] font-mono font-semibold bg-accent/15 text-accent border border-accent/30">
                  k-Anonymous Telemetry
                </span>
              </div>
              <p className="text-xs text-textSecondary mt-0.5 font-mono">
                Longitudinal wellness trends, cross-company strain comparisons, and ML feature associations
              </p>
            </div>
          </div>
        </div>

        {/* Full Advanced Commander Analytics Panel */}
        <AdvancedCommanderAnalytics />
      </div>
    </DashboardLayout>
  );
}
