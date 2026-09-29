'use client';

import React from 'react';
import { useAuth } from '@/lib/AuthContext';
import { LogOut, ShieldCheck, MapPin } from 'lucide-react';

export default function Topbar() {
  const { user, role, logout } = useAuth();

  const scopeTitle = user?.battalion && user?.location
    ? `${user.battalion} (${user.location}) • Operational Telemetry & Welfare Command`
    : role === 'admin'
    ? 'National Force Command • System Telemetry'
    : 'Operational Telemetry & Welfare Command';

  return (
    <header className="h-16 border-b border-surfaceBorder bg-surface flex items-center justify-between px-6 shrink-0">
      <div className="flex items-center space-x-3">
        <h2 className="text-sm md:text-base font-semibold text-textPrimary tracking-tight uppercase">
          {scopeTitle}
        </h2>
        {user && (
          <span className="hidden md:inline-flex items-center px-2 py-0.5 rounded text-[10px] font-mono font-medium bg-surfaceHighlight border border-surfaceBorder text-accent">
            <ShieldCheck className="w-3 h-3 mr-1 text-[#60987A]" />
            {role.toUpperCase()}
          </span>
        )}
        {user?.battalion && user?.location && (
          <span className="hidden lg:inline-flex items-center px-2 py-0.5 rounded text-[10px] font-mono font-medium bg-accent/15 border border-accent/30 text-accent">
            <MapPin className="w-3 h-3 mr-1 text-accent" />
            {user.battalion} • {user.location}
          </span>
        )}
      </div>

      <div className="flex items-center space-x-4">
        {user ? (
          <div className="flex items-center space-x-3">
            <div className="hidden sm:flex flex-col text-right">
              <span className="text-xs font-semibold text-textPrimary">{user.username}</span>
              <span className="text-[10px] font-mono text-accent uppercase font-bold">{role}</span>
            </div>
            <button
              onClick={logout}
              title="Sign Out"
              className="p-1.5 px-2.5 hover:bg-[#FAF0F0] rounded-lg text-textSecondary hover:text-[#964747] transition-colors flex items-center space-x-1.5 border border-transparent hover:border-[#E8B4B4]"
            >
              <LogOut className="w-3.5 h-3.5" />
              <span className="text-xs hidden sm:inline">Logout</span>
            </button>
          </div>
        ) : null}
      </div>
    </header>
  );
}
