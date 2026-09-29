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
  Menu,
} from 'lucide-react';
import { useAuth } from '@/lib/AuthContext';

export default function Sidebar() {
  const pathname = usePathname();
  const { logout, role, user } = useAuth();
  
  // Sidebar state: true = expanded (drawer open), false = collapsed (drawer closed)
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  const isOverview = pathname === '/dashboard' || pathname === '/dashboard/overview' || pathname === '/';
  const isPersonnel = pathname.startsWith('/personnel');
  const isAlerts = pathname.startsWith('/dashboard/alerts');
  const isSignals = pathname.startsWith('/dashboard/signals');
  const isRecommendations = pathname.startsWith('/dashboard/recommendations');
  const isAnalytics = pathname.startsWith('/dashboard/analytics');

  return (
    <aside 
      className={`${isSidebarOpen ? 'w-64' : 'w-20'} border-r border-surfaceBorder bg-surface flex flex-col h-full shrink-0 transition-all duration-300 relative`}
    >
      <div className={`h-20 flex items-center ${isSidebarOpen ? 'justify-between px-4 sm:px-5' : 'justify-center'} border-b border-surfaceBorder relative`}>
        {isSidebarOpen ? (
          <div className="flex items-center">
            <div className="w-12 h-12 sm:w-14 sm:h-14 flex items-center justify-center mr-3 shrink-0">
              <img src="/logo.png" alt="ManoBal Logo" className="w-full h-full object-contain drop-shadow-sm" />
            </div>
            <div>
              <h1 className="font-bold text-textPrimary tracking-wider uppercase text-sm sm:text-base leading-tight">
                ManoBal
              </h1>
              <p className="text-[10px] text-textSecondary uppercase font-mono tracking-widest mt-0.5">
                Command
              </p>
            </div>
          </div>
        ) : null}

        <button 
          onClick={() => setIsSidebarOpen(!isSidebarOpen)}
          className="flex items-center justify-center p-2 rounded-lg hover:bg-surfaceHighlight transition-all shrink-0 cursor-pointer"
          title={isSidebarOpen ? "Collapse Sidebar" : "Expand Sidebar"}
        >
          {isSidebarOpen ? (
            <svg width="34" height="22" viewBox="0 0 900 600" className="rounded-sm shadow-sm overflow-hidden" xmlns="http://www.w3.org/2000/svg">
              <rect width="900" height="200" fill="#FF9933"/>
              <rect y="200" width="900" height="200" fill="#FFFFFF"/>
              <rect y="400" width="900" height="200" fill="#138808"/>
              <circle cx="450" cy="300" r="80" fill="none" stroke="#000080" strokeWidth="12"/>
              <circle cx="450" cy="300" r="15" fill="#000080"/>
            </svg>
          ) : (
            <svg width="30" height="22" viewBox="0 0 20 16" fill="none" xmlns="http://www.w3.org/2000/svg">
              <rect width="20" height="3.5" rx="1.5" fill="#FF9933"/>
              <rect y="6.25" width="20" height="3.5" rx="1.5" fill="#FFFFFF" stroke="#CBD5E1" strokeWidth="1"/>
              <rect y="12.5" width="20" height="3.5" rx="1.5" fill="#138808"/>
            </svg>
          )}
        </button>
      </div>

      <nav className={`flex-1 overflow-y-auto py-4 ${isSidebarOpen ? 'px-3' : 'px-2'} space-y-6 overflow-x-hidden`}>
        {/* Main Navigation */}
        <div>
          <div className={`pb-2 uppercase font-mono font-bold tracking-widest text-textSecondary ${isSidebarOpen ? 'px-3 text-[10px]' : 'text-center text-[8px]'}`}>
            {isSidebarOpen ? 'Command & Roster' : 'CMD'}
          </div>
          <ul className="space-y-1">
            <li>
              <Link
                href="/dashboard"
                title="Dashboard Overview"
                className={`flex items-center ${isSidebarOpen ? 'px-3 py-2' : 'justify-center py-3'} text-sm font-medium rounded-lg transition-colors ${
                  isOverview
                    ? 'bg-surfaceHighlight text-textPrimary border-l-2 border-accent font-semibold'
                    : 'text-textSecondary hover:bg-surfaceHighlight hover:text-textPrimary'
                }`}
              >
                <Activity className={`w-5 h-5 ${isSidebarOpen ? 'mr-3' : ''} text-accent shrink-0`} />
                {isSidebarOpen && <span className="truncate">Dashboard Overview</span>}
              </Link>
            </li>
            <li>
              <Link
                href="/personnel"
                title="Personnel Directory"
                className={`flex items-center ${isSidebarOpen ? 'px-3 py-2' : 'justify-center py-3'} text-sm font-medium rounded-lg transition-colors ${
                  isPersonnel
                    ? 'bg-surfaceHighlight text-textPrimary border-l-2 border-accent font-semibold'
                    : 'text-textSecondary hover:bg-surfaceHighlight hover:text-textPrimary'
                }`}
              >
                <Users className={`w-5 h-5 ${isSidebarOpen ? 'mr-3' : ''} text-accent shrink-0`} />
                {isSidebarOpen && <span className="truncate">Personnel Directory</span>}
              </Link>
            </li>
          </ul>
        </div>

        {/* Telemetry Sections */}
        <div>
          <div className={`pb-2 uppercase font-mono font-bold tracking-widest text-textSecondary ${isSidebarOpen ? 'px-3 text-[10px]' : 'text-center text-[8px]'}`}>
            {isSidebarOpen ? 'Telemetry & Welfare' : 'TEL'}
          </div>
          <ul className="space-y-1">
            <li>
              <Link
                href="/dashboard/alerts"
                title="Welfare Alerts"
                className={`flex items-center ${isSidebarOpen ? 'px-3 py-2' : 'justify-center py-3'} text-sm font-medium rounded-lg transition-colors ${
                  isAlerts
                    ? 'bg-surfaceHighlight text-textPrimary border-l-2 border-accent font-semibold'
                    : 'text-textSecondary hover:bg-surfaceHighlight hover:text-textPrimary'
                }`}
              >
                <HeartPulse className={`w-5 h-5 ${isSidebarOpen ? 'mr-3' : ''} text-alert-rose shrink-0`} />
                {isSidebarOpen && <span className="truncate">Welfare Alerts</span>}
              </Link>
            </li>
            <li>
              <Link
                href="/dashboard/signals"
                title="Early-Warning Signals"
                className={`flex items-center ${isSidebarOpen ? 'px-3 py-2' : 'justify-center py-3'} text-sm font-medium rounded-lg transition-colors ${
                  isSignals
                    ? 'bg-surfaceHighlight text-textPrimary border-l-2 border-accent font-semibold'
                    : 'text-textSecondary hover:bg-surfaceHighlight hover:text-textPrimary'
                }`}
              >
                <Radar className={`w-5 h-5 ${isSidebarOpen ? 'mr-3' : ''} text-accent shrink-0`} />
                {isSidebarOpen && <span className="truncate">Early-Warning Signals</span>}
              </Link>
            </li>
            <li>
              <Link
                href="/dashboard/recommendations"
                title="Welfare Recommendations"
                className={`flex items-center ${isSidebarOpen ? 'px-3 py-2' : 'justify-center py-3'} text-sm font-medium rounded-lg transition-colors ${
                  isRecommendations
                    ? 'bg-surfaceHighlight text-textPrimary border-l-2 border-accent font-semibold'
                    : 'text-textSecondary hover:bg-surfaceHighlight hover:text-textPrimary'
                }`}
              >
                <Sparkles className={`w-5 h-5 ${isSidebarOpen ? 'mr-3' : ''} text-alert-amber shrink-0`} />
                {isSidebarOpen && <span className="truncate">Welfare Recommendations</span>}
              </Link>
            </li>
            <li>
              <Link
                href="/dashboard/analytics"
                title="Unit Welfare Analytics"
                className={`flex items-center ${isSidebarOpen ? 'px-3 py-2' : 'justify-center py-3'} text-sm font-medium rounded-lg transition-colors ${
                  isAnalytics
                    ? 'bg-surfaceHighlight text-textPrimary border-l-2 border-accent font-semibold'
                    : 'text-textSecondary hover:bg-surfaceHighlight hover:text-textPrimary'
                }`}
              >
                <BarChart3 className={`w-5 h-5 ${isSidebarOpen ? 'mr-3' : ''} text-accent shrink-0`} />
                {isSidebarOpen && <span className="truncate">Unit Welfare Analytics</span>}
              </Link>
            </li>
          </ul>
        </div>
      </nav>

      {/* User Role Card & Sign Out */}
      <div className={`p-4 border-t border-surfaceBorder space-y-2.5 ${!isSidebarOpen ? 'flex flex-col items-center' : ''}`}>
        {isSidebarOpen ? (
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
        ) : (
          <div className="w-10 h-10 rounded-full bg-accent/15 flex items-center justify-center text-accent font-bold mb-2 shrink-0 border border-accent/25" title={user?.username || 'Officer'}>
            {role?.charAt(0).toUpperCase() || 'O'}
          </div>
        )}
        <button
          onClick={logout}
          title="Sign Out"
          className={`flex items-center justify-center py-2 text-sm font-medium rounded-lg text-textSecondary hover:bg-[#FAF0F0] hover:text-[#964747] transition-colors ${isSidebarOpen ? 'w-full px-3' : 'w-10 h-10'}`}
        >
          <LogOut className={`w-5 h-5 ${isSidebarOpen ? 'mr-3' : ''}`} />
          {isSidebarOpen && <span>Sign Out</span>}
        </button>
      </div>
    </aside>
  );
}
