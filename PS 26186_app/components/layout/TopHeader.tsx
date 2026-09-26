'use client';

import React from 'react';
import { useAuth } from '@/lib/AuthContext';
import { LogOut, User } from 'lucide-react';

export default function TopHeader({ title }: { title: string }) {
  const { user, logout } = useAuth();

  return (
    <header className="flex items-center justify-between px-6 h-20 bg-gradient-to-b from-[var(--color-military-900)] to-transparent shrink-0">
      <div className="flex items-center space-x-2">
        <h1 className="text-lg font-semibold text-offwhite tracking-wide">{title}</h1>
      </div>

      {user && (
        <div className="flex items-center space-x-3 text-xs">
          <div className="flex items-center space-x-1 text-slate-400">
            <User className="w-3.5 h-3.5 text-teal-400" />
            <span className="font-mono text-[11px] text-slate-200">{user.username}</span>
          </div>
          <button
            onClick={logout}
            title="Sign Out"
            className="p-1 hover:bg-slate-800 rounded text-slate-400 hover:text-red-400 transition-colors"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      )}
    </header>
  );
}
