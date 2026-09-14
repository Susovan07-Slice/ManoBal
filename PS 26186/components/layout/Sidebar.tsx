import React from 'react';
import { ShieldAlert, Users, Activity, Settings, FileText } from 'lucide-react';

export default function Sidebar() {
  return (
    <aside className="w-64 border-r border-surfaceHighlight bg-surface flex flex-col h-full shrink-0">
      <div className="h-16 flex items-center px-6 border-b border-surfaceHighlight">
        <ShieldAlert className="text-accent w-6 h-6 mr-2" />
        <h1 className="font-bold text-textPrimary tracking-wider uppercase text-sm">Command Center</h1>
      </div>
      
      <nav className="flex-1 overflow-y-auto py-4">
        <ul className="space-y-1 px-3">
          <li>
            <a href="#" className="flex items-center px-3 py-2 text-sm font-medium rounded bg-surfaceHighlight text-textPrimary text-accent-light">
              <Activity className="w-4 h-4 mr-3" />
              Overview
            </a>
          </li>
          <li>
            <a href="#" className="flex items-center px-3 py-2 text-sm font-medium rounded text-textSecondary hover:bg-surfaceHighlight hover:text-textPrimary transition-colors">
              <Users className="w-4 h-4 mr-3" />
              Unit Rosters
            </a>
          </li>
          <li>
            <a href="#" className="flex items-center px-3 py-2 text-sm font-medium rounded text-textSecondary hover:bg-surfaceHighlight hover:text-textPrimary transition-colors">
              <FileText className="w-4 h-4 mr-3" />
              {/* TODO Phase 3: Role-based navigation items (e.g. Case Log for Welfare Officer) */}
              Reports
            </a>
          </li>
        </ul>
      </nav>

      <div className="p-4 border-t border-surfaceHighlight">
        <a href="#" className="flex items-center px-3 py-2 text-sm font-medium rounded text-textSecondary hover:bg-surfaceHighlight hover:text-textPrimary transition-colors">
          <Settings className="w-4 h-4 mr-3" />
          Settings
        </a>
      </div>
    </aside>
  );
}
