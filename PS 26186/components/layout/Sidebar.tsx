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
  FileText,
  Info,
  Sliders,
  BarChart3,
  Radar,
} from 'lucide-react';
import { useAuth } from '@/lib/AuthContext';

export default function Sidebar() {
  const pathname = usePathname();
  const { logout, role, user } = useAuth();
  const [showProtocolModal, setShowProtocolModal] = useState(false);

  const isOverview = pathname === '/dashboard' || pathname === '/';
  const isPersonnel = pathname.startsWith('/personnel');

  return (
    <>
      <aside className="w-64 border-r border-surfaceHighlight bg-surface flex flex-col h-full shrink-0">
        <div className="h-16 flex items-center px-6 border-b border-surfaceHighlight">
          <div className="w-8 h-8 rounded-lg bg-accent/15 border border-accent/30 flex items-center justify-center mr-3 shrink-0">
            <ShieldAlert className="text-accent w-4 h-4" />
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
                      ? 'bg-surfaceHighlight text-textPrimary border-l-2 border-accent'
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
                      ? 'bg-surfaceHighlight text-textPrimary border-l-2 border-accent'
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
                  href="/dashboard#telemetry-distributions"
                  className="flex items-center px-3 py-2 text-sm font-medium rounded-lg text-textSecondary hover:bg-surfaceHighlight hover:text-textPrimary transition-colors"
                >
                  <Activity className="w-4 h-4 mr-3 text-emerald-400" />
                  Stress Distribution
                </Link>
              </li>
              <li>
                <Link
                  href="/dashboard#telemetry-distributions"
                  className="flex items-center px-3 py-2 text-sm font-medium rounded-lg text-textSecondary hover:bg-surfaceHighlight hover:text-textPrimary transition-colors"
                >
                  <Shield className="w-4 h-4 mr-3 text-amber-400" />
                  Risk Priority Stance
                </Link>
              </li>
              <li>
                <Link
                  href="/dashboard#risk-alerts-table"
                  className="flex items-center px-3 py-2 text-sm font-medium rounded-lg text-textSecondary hover:bg-surfaceHighlight hover:text-textPrimary transition-colors"
                >
                  <HeartPulse className="w-4 h-4 mr-3 text-rose-400" />
                  Welfare Alerts
                </Link>
              </li>
              <li>
                <Link
                  href="/dashboard#advanced-analytics"
                  className="flex items-center px-3 py-2 text-sm font-medium rounded-lg text-textSecondary hover:bg-surfaceHighlight hover:text-textPrimary transition-colors"
                >
                  <BarChart3 className="w-4 h-4 mr-3 text-cyan-400" />
                  Unit Welfare Analytics
                </Link>
              </li>
              <li>
                <Link
                  href="/dashboard#early-warning-signals"
                  className="flex items-center px-3 py-2 text-sm font-medium rounded-lg text-textSecondary hover:bg-surfaceHighlight hover:text-textPrimary transition-colors"
                >
                  <Radar className="w-4 h-4 mr-3 text-rose-400" />
                  Early-Warning Signals
                </Link>
              </li>
            </ul>
          </div>

          {/* Documentation & Research */}
          <div>
            <div className="px-3 pb-2 text-[10px] uppercase font-mono font-bold tracking-widest text-textSecondary">
              System Governance
            </div>
            <ul className="space-y-1">
              <li>
                <button
                  type="button"
                  onClick={() => setShowProtocolModal(true)}
                  className="w-full flex items-center px-3 py-2 text-sm font-medium rounded-lg text-textSecondary hover:bg-surfaceHighlight hover:text-textPrimary transition-colors text-left"
                >
                  <FileText className="w-4 h-4 mr-3 text-teal-400" />
                  Protocol & Disclaimer
                </button>
              </li>
            </ul>
          </div>
        </nav>

        {/* User Role Card & Sign Out */}
        <div className="p-4 border-t border-surfaceHighlight space-y-2.5">
          <div className="px-3 py-2 text-xs font-mono text-textSecondary bg-surfaceHighlight/50 rounded-lg border border-surfaceHighlight">
            <div className="flex items-center justify-between">
              <span className="text-[10px] uppercase tracking-wider text-textSecondary">Active Role</span>
              <span className="text-[10px] px-1.5 py-0.2 rounded bg-accent/20 text-accent font-semibold uppercase">
                {role}
              </span>
            </div>
            <div className="text-textPrimary font-semibold text-xs mt-1 truncate">
              {user?.username || 'Authenticated Officer'}
            </div>
          </div>
          <button
            onClick={logout}
            className="w-full flex items-center px-3 py-2 text-sm font-medium rounded-lg text-textSecondary hover:bg-surfaceHighlight hover:text-rose-400 transition-colors"
          >
            <LogOut className="w-4 h-4 mr-3" />
            Sign Out
          </button>
        </div>
      </aside>

      {/* Protocol / Disclaimer Modal */}
      {showProtocolModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-surface border border-surfaceHighlight rounded-xl max-w-lg w-full p-6 space-y-4 shadow-2xl">
            <div className="flex justify-between items-start">
              <div className="flex items-center space-x-2">
                <Info className="w-5 h-5 text-accent" />
                <h3 className="font-bold text-base text-textPrimary uppercase tracking-wider">
                  Operational AI Safety & Protocols
                </h3>
              </div>
              <button
                onClick={() => setShowProtocolModal(false)}
                className="text-textSecondary hover:text-textPrimary text-sm font-mono px-2 py-1 bg-surfaceHighlight rounded"
              >
                ✕
              </button>
            </div>

            <div className="space-y-3 text-xs text-textSecondary leading-relaxed">
              <p>
                <strong className="text-textPrimary">Research Prototype Context:</strong> ManoBal is an AI-based predictive personnel stress and operational welfare monitoring decision-support system designed for uniformed force command and welfare officers.
              </p>
              <div className="p-3 bg-surfaceHighlight/40 rounded-lg border border-surfaceHighlight space-y-1">
                <div className="font-semibold text-textPrimary uppercase tracking-wider text-[11px]">
                  Ethical Safeguards:
                </div>
                <ul className="list-disc pl-4 space-y-1 text-[11px]">
                  <li>Non-punitive: Insights are purely for supportive rest rotation and welfare intervention.</li>
                  <li>Decision-Support: Machine learning outputs do not constitute clinical or medical diagnoses.</li>
                  <li>Synthetic Data: Demonstrations use synthetically augmented research datasets; no live CRPF records.</li>
                  <li>Explainability: TreeSHAP feature associations provide transparent rationales for each prediction.</li>
                </ul>
              </div>
              <p className="text-[11px] text-textSecondary italic">
                Active Architecture: LightGBM Multiclass Model • TreeSHAP Explainability • Continuous Risk Index [0–100] • Role-Based Access Control (RBAC).
              </p>
            </div>

            <div className="pt-2 flex justify-end">
              <button
                onClick={() => setShowProtocolModal(false)}
                className="px-4 py-2 bg-accent hover:bg-accent/80 text-white rounded-lg text-xs font-semibold uppercase tracking-wider"
              >
                Acknowledge Protocol
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
