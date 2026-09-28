'use client';

import React from 'react';
import Link from 'next/link';
import DashboardLayout from '@/components/layout/DashboardLayout';
import EarlyWarningSignalsPanel from '@/components/dashboard/EarlyWarningSignalsPanel';
import { Radar, ArrowLeft, Info } from 'lucide-react';

export default function EarlyWarningSignalsPage() {
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
                  Early-Warning Signals Radar
                </h1>
                <span className="px-2 py-0.5 rounded text-[10px] font-mono font-semibold bg-accent/15 text-accent border border-accent/30">
                  Anomaly Detection
                </span>
              </div>
              <p className="text-xs text-textSecondary mt-0.5 font-mono">
                Multi-dimensional behavioral deviation radar and longitudinal escalation detectors
              </p>
            </div>
          </div>
        </div>

        {/* Full Interactive Radar & Anomaly Signals Panel */}
        <EarlyWarningSignalsPanel />
      </div>
    </DashboardLayout>
  );
}
