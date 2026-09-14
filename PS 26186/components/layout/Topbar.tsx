import React from 'react';
import RoleToggle from './RoleToggle';

export default function Topbar() {
  return (
    <header className="h-16 border-b border-surfaceHighlight bg-surface flex items-center justify-between px-6">
      <div className="flex items-center">
        {/* TODO Phase 3: Display dynamic unit name based on selection/data */}
        <h2 className="text-lg font-semibold text-textPrimary tracking-tight">7th Battalion, Bravo Company</h2>
      </div>
      <div className="flex items-center space-x-4">
        <span className="text-sm text-textSecondary font-mono hidden sm:inline-block">SYS_TIME: <span className="text-textPrimary">{new Date().toISOString().split('T')[0]}</span></span>
        <RoleToggle />
      </div>
    </header>
  );
}
