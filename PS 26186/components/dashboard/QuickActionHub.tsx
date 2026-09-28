'use client';

import React from 'react';
import Link from 'next/link';
import {
  Bell,
  Radar,
  HeartPulse,
  BarChart3,
  Users,
  ArrowUpRight,
  ShieldCheck,
} from 'lucide-react';

interface QuickActionHubProps {
  urgentAlertsCount?: number;
  recommendationsCount?: number;
  signalsCount?: number;
}

export default function QuickActionHub({
  urgentAlertsCount = 0,
  recommendationsCount = 0,
  signalsCount = 0,
}: QuickActionHubProps) {
  const hubs = [
    {
      title: 'Welfare Alerts & Requests',
      description: 'Review pending jawan inquiries & urgent stress alerts',
      href: '/dashboard/alerts',
      icon: Bell,
      badge: urgentAlertsCount > 0 ? `${urgentAlertsCount} Urgent` : 'Up to date',
      badgeColor: urgentAlertsCount > 0 ? 'bg-alert-roseBg text-alert-roseText' : 'bg-alert-sageBg text-alert-sageText',
    },
    {
      title: 'Early-Warning Signals',
      description: 'Multi-dimensional strain radar & anomaly indicators',
      href: '/dashboard/signals',
      icon: Radar,
      badge: signalsCount > 0 ? `${signalsCount} Signals` : 'Monitoring',
      badgeColor: 'bg-surfaceHighlight text-textSecondary',
    },
    {
      title: 'Welfare Recommendations',
      description: 'Non-punitive AI-suggested interventions & protocols',
      href: '/dashboard/recommendations',
      icon: HeartPulse,
      badge: recommendationsCount > 0 ? `${recommendationsCount} Active` : 'Review',
      badgeColor: 'bg-alert-amberBg text-alert-amberText',
    },
    {
      title: 'Unit Welfare Analytics',
      description: 'Longitudinal fatigue trends & k-anonymous intelligence',
      href: '/dashboard/analytics',
      icon: BarChart3,
      badge: 'Aggregated',
      badgeColor: 'bg-surfaceHighlight text-textSecondary',
    },
  ];

  return (
    <div className="bg-surface border border-surfaceBorder rounded-2xl p-5 shadow-card flex flex-col justify-between h-full">
      <div>
        <div className="flex items-center justify-between pb-3 mb-4 border-b border-surfaceBorder">
          <div>
            <h3 className="text-sm font-bold text-textPrimary tracking-tight">
              Command Modules & Workflows
            </h3>
            <p className="text-[11px] text-textSecondary font-mono">
              Dedicated operational workspaces for unit commanders & welfare officers
            </p>
          </div>
          <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-surfaceHighlight text-textSecondary">
            Direct Access
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {hubs.map((hub) => {
            const Icon = hub.icon;
            return (
              <Link
                key={hub.href}
                href={hub.href}
                className="group p-3.5 bg-surfaceHighlight/30 hover:bg-surfaceHighlight/80 border border-surfaceBorder rounded-xl transition-all duration-150 flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <div className="w-8 h-8 rounded-lg bg-surface border border-surfaceBorder flex items-center justify-center text-accent group-hover:scale-105 transition-transform">
                      <Icon className="w-4 h-4" />
                    </div>
                    <span className={`text-[10px] font-mono font-semibold px-2 py-0.5 rounded-full ${hub.badgeColor}`}>
                      {hub.badge}
                    </span>
                  </div>
                  <h4 className="text-xs font-bold text-textPrimary group-hover:text-accent transition-colors flex items-center justify-between">
                    <span>{hub.title}</span>
                    <ArrowUpRight className="w-3.5 h-3.5 opacity-40 group-hover:opacity-100 transition-opacity" />
                  </h4>
                  <p className="text-[11px] text-textSecondary mt-1 leading-relaxed">
                    {hub.description}
                  </p>
                </div>
              </Link>
            );
          })}
        </div>
      </div>

      <div className="pt-3 mt-4 border-t border-surfaceBorder flex items-center justify-between text-xs">
        <span className="text-[11px] text-textSecondary font-mono">
          Personnel Roster
        </span>
        <Link
          href="/personnel"
          className="inline-flex items-center space-x-1 font-semibold text-accent hover:text-accent-hover transition-colors"
        >
          <Users className="w-3.5 h-3.5" />
          <span>Open Full Personnel Directory</span>
        </Link>
      </div>
    </div>
  );
}
