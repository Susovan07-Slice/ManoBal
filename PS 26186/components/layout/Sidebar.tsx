import React, { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  ShieldAlert,
  Users,
  Activity,
  LogOut,
  Shield,
  HeartPulse,
  BarChart3,
  Radar,
  Sparkles,
} from 'lucide-react';
import { useAuth } from '@/lib/AuthContext';

export default function Sidebar() {
  const pathname = usePathname();
  const { logout, role, user } = useAuth();

  const isOverview = pathname === '/dashboard' || pathname === '/dashboard/overview' || pathname === '/';
  const isPersonnel = pathname.startsWith('/personnel');
  const isAlerts = pathname.startsWith('/dashboard/alerts');
  const isSignals = pathname.startsWith('/dashboard/signals');
  const isRecommendations = pathname.startsWith('/dashboard/recommendations');
  const isAnalytics = pathname.startsWith('/dashboard/analytics');

  return (
    <aside className="w-64 border-r border-surfaceBorder bg-surface flex flex-col h-full shrink-0">
        <div className="h-20 flex items-center px-6 border-b border-surfaceBorder">
          <div className="w-16 h-16 flex items-center justify-center mr-4 shrink-0 overflow-hidden rounded-full">
            <img src="/logo.png" alt="ManoBal Logo" className="w-full h-full object-cover scale-110 drop-shadow-sm" />
          </div>
          <div>
            <h1 className="font-bold text-textPrimary tracking-wider uppercase text-sm leading-tight">
              ManoBal
            </h1>
            <p className="text-[10px] text-textSecondary uppercase font-mono tracking-widest">
              Command Center
            </p>
          </div>
        </div>

        <nav className="flex-1 overflow-y-auto py-4 px-3 space-y-6">
          {/* Main Navigation */}
          <div>
            <div className="px-3 pb-2 text-[10px] uppercase font-mono font-bold tracking-widest text-textSecondary">
              Command & Roster
            </div>
            <ul className="space-y-1">
              <li>
                <Link
                  href="/dashboard"
                  className={`flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors ${
                    isOverview
                      ? 'bg-surfaceHighlight text-textPrimary border-l-2 border-accent font-semibold'
                      : 'text-textSecondary hover:bg-surfaceHighlight hover:text-textPrimary'
                  }`}
                >
                  <Activity className="w-4 h-4 mr-3 text-accent" />
                  Dashboard Overview
                </Link>
              </li>
              <li>
                <Link
                  href="/personnel"
                  className={`flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors ${
                    isPersonnel
                      ? 'bg-surfaceHighlight text-textPrimary border-l-2 border-accent font-semibold'
                      : 'text-textSecondary hover:bg-surfaceHighlight hover:text-textPrimary'
                  }`}
                >
                  <Users className="w-4 h-4 mr-3 text-accent" />
                  Personnel Directory
                </Link>
              </li>
            </ul>
          </div>

          {/* Telemetry Sections */}
          <div>
            <div className="px-3 pb-2 text-[10px] uppercase font-mono font-bold tracking-widest text-textSecondary">
              Telemetry & Welfare
            </div>
            <ul className="space-y-1">
              <li>
                <Link
                  href="/dashboard/alerts"
                  className={`flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors ${
                    isAlerts
                      ? 'bg-surfaceHighlight text-textPrimary border-l-2 border-accent font-semibold'
                      : 'text-textSecondary hover:bg-surfaceHighlight hover:text-textPrimary'
                  }`}
                >
                  <HeartPulse className="w-4 h-4 mr-3 text-alert-rose" />
                  Welfare Alerts
                </Link>
              </li>
              <li>
                <Link
                  href="/dashboard/signals"
                  className={`flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors ${
                    isSignals
                      ? 'bg-surfaceHighlight text-textPrimary border-l-2 border-accent font-semibold'
                      : 'text-textSecondary hover:bg-surfaceHighlight hover:text-textPrimary'
                  }`}
                >
                  <Radar className="w-4 h-4 mr-3 text-accent" />
                  Early-Warning Signals
                </Link>
              </li>
              <li>
                <Link
                  href="/dashboard/recommendations"
                  className={`flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors ${
                    isRecommendations
                      ? 'bg-surfaceHighlight text-textPrimary border-l-2 border-accent font-semibold'
                      : 'text-textSecondary hover:bg-surfaceHighlight hover:text-textPrimary'
                  }`}
                >
                  <Sparkles className="w-4 h-4 mr-3 text-alert-amber" />
                  Welfare Recommendations
                </Link>
              </li>
              <li>
                <Link
                  href="/dashboard/analytics"
                  className={`flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors ${
                    isAnalytics
                      ? 'bg-surfaceHighlight text-textPrimary border-l-2 border-accent font-semibold'
                      : 'text-textSecondary hover:bg-surfaceHighlight hover:text-textPrimary'
                  }`}
                >
                  <BarChart3 className="w-4 h-4 mr-3 text-accent" />
                  Unit Welfare Analytics
                </Link>
              </li>
            </ul>
          </div>
        </nav>

        {/* User Role Card & Sign Out */}
        <div className="p-4 border-t border-surfaceBorder space-y-2.5">
          <div className="px-3 py-2 text-xs font-mono text-textSecondary bg-surfaceHighlight/50 rounded-lg border border-surfaceBorder">
            <div className="flex items-center justify-between">
              <span className="text-[10px] uppercase tracking-wider text-textSecondary">Active Role</span>
              <span className="text-[10px] px-1.5 py-0.2 rounded bg-accent/15 text-accent font-semibold uppercase border border-accent/25">
                {role}
              </span>
            </div>
            <div className="text-textPrimary font-semibold text-xs mt-1 truncate">
              {user?.username || 'Authenticated Officer'}
            </div>
          </div>
          <button
            onClick={logout}
            className="w-full flex items-center px-3 py-2 text-sm font-medium rounded-lg text-textSecondary hover:bg-[#FAF0F0] hover:text-[#964747] transition-colors"
          >
            <LogOut className="w-4 h-4 mr-3" />
            Sign Out
          </button>
        </div>
      </aside>
  );
}
